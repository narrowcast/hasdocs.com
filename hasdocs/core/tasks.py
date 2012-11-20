import logging
import os
import subprocess
import tarfile

import requests
from celery import chain, task

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage

from hasdocs.projects.models import Project

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
    payload = {'access_token': '7e427d2761a94514af800a6c5bc7f33d4326656f'}
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
    print filename
    tar = tarfile.open(filename)
    path = tar.next().path
    tar.extractall()
    tar.close()
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
    return result

@task
def upload_docs(result, project):
    """Uploads the built docs to the appropriate storage."""
    logger.info('Uploading docs for %s' % project)
    #count = 0
    #for root, dirs, names in os.walk('docs/_build/html'):
    #    for idx, name in enumerate(names):
    #        with open(os.path.join(root, name), 'rb') as f:
    #            file = File(f)
                #default_storage.save('/docs/%s/%s' % project.owner, project,
                #                     file.name, file)
                # Deletes the file after uploading
    #            file.delete()
    #    count += idx
    #logger.info('Finished uploading %s files' % count)