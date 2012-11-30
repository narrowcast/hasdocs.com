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
        create_virtualenv.s(project),
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
    with open(filename, 'wb') as file:
        file.write(r.content)
    return filename

@task
def extract(filename, project):
    """Extracts the given tarball and returns its resulting path."""
    logger.debug('Extracting %s', filename)
    try:
        with tarfile.open(filename) as tar:
            path = tar.next().path
            tar.extractall()
    except tarfile.ReadError:
        logger.error('Error opening file %s' % filename)
    os.remove(filename)
    return path

@task
def create_virtualenv(path, project):
    logger.info('Creating virtualenv for %s/%s' % (project.owner, project.name))
    try:
        subprocess.check_call(['bash', 'bin/detect', path])
    except subprocess.CalledProcessError:
        logger.warning('Sphinx documentation could not be detected.')
    # Check if the virtualenv is stored in S3    
    #try:
    #    venv = '%s/%s/venv.tar.gz' % (project.owner, project.name)
    #    with docs_storage.open(venv, 'r') as fp:
    #        with tarfile.open(fileobj=fp) as tar:
    #            tar.extractall(path)
    #except IOError:
    #    pass
    try:
        subprocess.check_call(['bash', 'bin/compile', path])
    except subprocess.CalledProcessError:
        logger.warning('Compilation failed.')    
    #with tarfile.open('%s/%s' % (path, venv), 'w:gz') as tar:
    #    tar.add('%s/venv' % path)
    #with open('%s/%s' % (path, venv), 'rb') as fp:
    #    file = File(fp)
    #    docs_storage.save(dest, file)
    #os.remove('%s/%s' % (path, venv))
    logger.info('Created virtualenv for %s/%s' % (project.owner, project.name))
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