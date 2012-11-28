import datetime
import logging
import os
import shutil
import subprocess
import tarfile

import requests
from celery import chain, task
from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.core.cache import cache
from django.core.files import File

logger = logging.getLogger(__name__)
docs_storage = S3BotoStorage(bucket=settings.AWS_DOCS_BUCKET_NAME, acl='private',
                             reduced_redundancy=True, secure_urls=False)

@task
def update_docs(project):
    """Fetches the source repo, builds docs and uploads them for serving."""
    result = chain(
        fetch_source.s(project),
        extract.s(project),
        build_docs.s(project),
        upload_docs.s(project)
    )()
    return result

@task
def fetch_source(project):
    """Fetchs the source from git repository."""
    logger.info('Fetching source for %s from GitHub' % project)
    # TODO: This cannot just be the project owner's token
    payload = {'access_token': project.owner.get_profile().github_access_token}
    r = requests.get('%s/repos/%s/%s/tarball' % (
        settings.GITHUB_API_URL, project.owner, project.name,
    ), params=payload)
    filename = '%s.tar.gz' % project
    file = open(filename, 'wb')
    file.write(r.content)
    file.close()
    return filename

@task
def extract(filename, project):
    """Extracts the given tarball and returns its resulting path."""
    logger.debug('Extracting %s', filename)
    try:
        tar = tarfile.open(filename)
        path = tar.next().path
        tar.extractall()
        tar.close()
    except tarfile.ReadError:
        logger.error('Error opening file %s' % filename)
    os.remove(filename)
    return path

@task
def build_docs(path, project):
    """Builds new docs using the appropriate autodoc module."""
    logger.info('Building docs for %s' % project)
    # TODO docs folder should not be hard-coded
    process = subprocess.Popen(['make', 'html'], cwd='%s/docs' % path)
    stdoutdata, stderrdata = process.communicate()
    return path

@task
def upload_docs(path, project):
    """Uploads the built docs to the appropriate storage."""
    logger.info('Uploading docs for %s' % project)
    count = 0
    dest_base = '%s/%s' % (project.owner, project)
    local_base = '%s/docs/_build/html/' % path    
    # Walks through the built doc files and uploads them
    for root, dirs, names in os.walk(local_base):
        for idx, name in enumerate(names):
            with open(os.path.join(root, name), 'rb') as fp:
                file = File(fp)
                dest = '%s/%s' % (dest_base, os.path.relpath(file.name, local_base))
                logger.info('Uploading %s...' % dest)
                docs_storage.save(dest, file)
                # Invalidates cache
                cache.delete(dest)
                # Deletes the file from local after uploading
                file.close()
                os.remove(os.path.join(root, name))
        count += idx
    shutil.rmtree(path)
    # Updates the project's modified date
    project.save()
    logger.info('Finished uploading %s files' % count)
    return count