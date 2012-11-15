import logging
import subprocess
import tarfile

from celery import task

from django.conf import settings

logger = logging.getLogger(__name__)


@task
def fetch_source(project):
    """Fetchs the source from git repository."""
    logger.info('Fetching source from ...')
    
    r = requests.get('%s/repos/%s/%s/tarball' % (
        settings.GITHUB_API_URL, project.owner, project.name
    ))
    
    logger.debug('storing %s into %s', commit, filename)
    f = open(filename, 'wb')
    f.write(r.content)
    f.close()

@task
def extract(filename):
    """Extracts the given tarball."""
    logger.debug('Extracting %s', filename)
    tar = tarfile.open(filename)
    tar.extractall(path)
    tar.close()

@task
def build_docs():
    """Builds new docs using the appropriate autodoc module."""
    logger.info('Building docs...')
    result = subprocess.check_output('sphinx-build %s -b html . _build/html')

@task
def update_docs():
    """Uploads the built docs to the appropriate storage."""
    pass