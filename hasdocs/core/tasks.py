import datetime
import logging
import os
import shutil
import subprocess
import tarfile

import requests
import virtualenv
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
    # Check if the virtualenv is stored in S3
    # WTF: This is gross
    python = '%s/venv/bin/python' % path
    pip = '%s/venv/bin/pip' % path
    venv = 'venv.tar.gz'
    dest = '%s/%s/%s' % (project.owner, project.name, venv)
    # WTF: This may cause problems with multiple workers
    pythonhome = os.environ.pop('PYTHONHOME')
    try:
        # If there is, retrieve it and extract it
        with docs_storage.open(path, 'r') as fp:
            with tarfile.open(fileobj=fp) as tar:
                tar.extractall(path)
    except IOError:
        # If not, create one by installing the dependencies
        virtualenv.create_environment('%s/venv' % path, use_distribute=True)
        subprocess.check_call([python, '%s/setup.py' % path, 'develop'])
        subprocess.check_call([pip, 'install', 'sphinx'])
    # Install additional dependencies, if any
    requirements = '%s/%s' % (path, 'requirements.txt')
    subprocess.check_call([pip, 'install', '-r', requirements])
    os.environ['PYTHONHOME'] = pythonhome
    with tarfile.open('%s/%s' % (path, venv), 'w:gz') as tar:
        tar.add('%s/venv' % path)
    with open('%s/%s' % (path, venv), 'rb') as fp:
        file = File(fp)
        docs_storage.save(dest, file)
    os.remove('%s/%s' % (path, venv))
    logger.info('Created virtualenv for %s/%s' % (project.owner, project.name))
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