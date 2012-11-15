import logging
import os
import subprocess
import tarfile

import requests
from celery import chain, task

from django.conf import settings

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
    r = requests.get('%s/repos/%s/%s/tarball' % (
        settings.GITHUB_API_URL, project.owner, project.name
    ))
    filename = '%s.tar.gz' % project
    f = open(filename, 'wb')
    f.write(r.content)
    f.close()
    return filename

@task
def extract(bytes_written, project):
    """Extracts the given tarball and returns its resulting path."""
    filename = '%s.tar.gz' % project
    logger.debug('Extracting %s', filename)
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
    result = subprocess.check_output(
        # This is ghetto, should fix asap
        ['sphinx-build', '-b', 'html', '%s/docs/' % path, '%s/docs/_build/html' % path]
    )
    logger.info(result)
    return result

@task
def upload_docs(result, project):
    """Uploads the built docs to the appropriate storage."""
    logger.info('Uploading docs for %s' % project)