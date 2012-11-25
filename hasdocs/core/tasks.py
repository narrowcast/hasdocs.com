import logging
import os
import shutil
import subprocess
import tarfile

import boto
import requests
from celery import chain, task

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


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
    builder = None
    if project.generator.name == 'Sphinx':
        builder = ['sphinx-build']
        args = ['-b', 'html', '%s/docs/' % path, '%s/docs/_build/html/' % path]
    result = subprocess.check_output(builder + args)
    logger.info(result)
    return path

@task
def upload_docs(path, project):
    """Uploads the built docs to the appropriate storage."""
    logger.info('Uploading docs for %s' % project)
    count = 0
    dest_base = '%s%s/%s/' % (settings.DOCS_URL, project.owner, project)
    local_base = '%s/docs/_build/html/' % path    
    # Walks through the built doc files and uploads them
    for root, dirs, names in os.walk(local_base):        
        for idx, name in enumerate(names):
            with open(os.path.join(root, name), 'rb') as f:
                file = File(f)
                dest = '%s%s' % (dest_base, os.path.relpath(file.name, local_base))
                #default_storage.save(dest, file)
                dest = boto.storage_uri('hasdocs.com/%s' % dest, 'gs')
                dest.new_key().set_contents_from_file(f)
                # Deletes the file from local after uploading
                file.close()
                os.remove(os.path.join(root, name))
        count += idx
    shutil.rmtree(path)
    logger.info('Finished uploading %s files' % count)
    return count
