import datetime
import logging
import os
import shutil
import subprocess
import tarfile

import requests
from celery import chain, task
from celery.utils.log import get_task_logger
from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.core.cache import cache
from django.core.files import File

logger = get_task_logger(__name__)

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
        # TODO: should revoke the task, clean up, and return
    os.remove(filename)
    return path

@task
def build_docs(path, project):
    logger.info('Building documentations for %s/%s' % (project.owner, project.name))
    # Check if the virtualenv is stored in S3
    dest = '%s/%s/%s' % (project.owner, project.name, settings.VENV_FILENAME)
    try:
        with docs_storage.open(dest, 'r') as fp:
            logger.info('Detected a previously stored virtualenv.')
            with tarfile.open(fileobj=fp) as tar:
                tar.extractall()
    except IOError:
        logger.info('No previously stored virtualenv was found.')
    try:
        subprocess.check_call(['bash', 'bin/compile', path, project.docs_path,
                               project.requirements.path])
        # Store the virtualenv in S3
        venv = '%s/%s' % (path, settings.VENV_FILENAME)
        logger.info('Storing virtualenv in S3')
        with tarfile.open(venv, 'w:gz') as tar:
            tar.add('%s/%s' % (path, settings.VENV_NAME))
        with open(venv, 'rb') as fp:
            file = File(fp)
            docs_storage.save(dest, file)
        os.remove(venv)
    except subprocess.CalledProcessError:
        logger.warning('Compilation failed for %s/%s.' % (project.owner, project.name))
        raise
    logger.info('Built docs for %s/%s' % (project.owner, project.name))
    return path

@task
def upload_docs(path, project):
    """Uploads the built docs to the appropriate storage."""
    logger.info('Uploading docs for %s' % project)
    count = 0
    dest_base = '%s/%s' % (project.owner, project.name)
    target = subprocess.check_output(['bash', 'bin/target', path, 'docs'])
    local_base = '%s/%s/html/' % (path, target)
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