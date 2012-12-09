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

from hasdocs.projects.models import Build

logger = get_task_logger(__name__)

docs_storage = S3BotoStorage(
    bucket=settings.AWS_DOCS_BUCKET_NAME, acl='private',
    reduced_redundancy=True, secure_urls=False
)


def update_docs(project):
    """Fetches the source repo, builds docs and uploads them for serving."""
    build = Build.objects.create(project=project, status=Build.UNKNOWN)
    logger.info('Build %s started' % build)
    chain(
        fetch_source.s(build, project),
        extract.s(project),
        build_docs.s(project),
        upload_docs.s(project)
    ).apply_async()


@task
def fetch_source(build, project):
    """Fetchs the source from git repository."""    
    logger.info('Fetching source for %s from GitHub' % project)
    # TODO: This cannot just be the project owner's token
    payload = {'access_token': project.owner.get_profile().github_access_token}
    r = requests.get('%s/repos/%s/%s/tarball' % (
        settings.GITHUB_API_URL, project.owner, project.name,
    ), params=payload)
    build.filename = '%s.tar.gz' % project
    with open(build.filename, 'wb') as file:
        file.write(r.content)
    return build


@task
def extract(build, project):
    """Extracts the given tarball and returns its resulting path."""
    logger.debug('Extracting %s', build.filename)
    try:
        with tarfile.open(build.filename) as tar:
            build.path = tar.next().path
            tar.extractall()
    except tarfile.ReadError:
        logger.error('Error opening file %s' % build.filename)
        # TODO: nicer handling of exception
        raise
    os.remove(build.filename)
    return build


@task
def create_virtualenv(build, project):
    """Retrives or creates the virtualenv for the project and stores it."""
    logger.info('Creating virtualenv for %s/%s' % (
        project.owner, project.name))
    pass


@task
def build_docs(build, project):
    """Builds the documentations for the projects."""
    # TODO: This function is way too long, decompose
    logger.info('Building documentation for %s/%s' % (
        project.owner, project.name))
    # Check if the virtualenv is stored in S3
    dest = '%s/%s/%s' % (project.owner, project.name, settings.VENV_FILENAME)
    try:
        with docs_storage.open(dest, 'r') as fp:
            logger.info('Detected a previously stored virtualenv')
            with tarfile.open(fileobj=fp) as tar:
                tar.extractall()
    except IOError:
        logger.info('No previously stored virtualenv was found')
    try:
        args = ['bash', 'bin/compile', build.path, project.docs_path,
                project.requirements_path]
        build.output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        build.save()
    except subprocess.CalledProcessError, e:
        logger.warning('Compilation failed for %s/%s' % (
            project.owner, project.name))
        build.output = e.output
        build.status = Build.FAILURE
        build.save()
        # TODO: nicer cleanup of mess on failure (maybe an error link)
        shutil.rmtree(build.path)
        # TODO: nicer handling of exception
        raise
    # Store the virtualenv in S3
    venv = '%s/%s' % (build.path, settings.VENV_FILENAME)
    logger.info('Storing virtualenv in S3')
    with tarfile.open(venv, 'w:gz') as tar:
        tar.add('%s/%s' % (build.path, settings.VENV_NAME))
    with open(venv, 'rb') as fp:
        file = File(fp)
        docs_storage.save(dest, file)
    os.remove(venv)
    logger.info('Built docs for %s/%s' % (project.owner, project.name))
    return build


@task
def upload_docs(build, project):
    """Uploads the built docs to the appropriate storage."""
    project = build.project
    logger.info('Uploading docs for %s' % project)
    count = 0
    dest_base = '%s/%s' % (project.owner, project.name)
    target = subprocess.check_output(
        ['bash', 'bin/target', build.path, project.docs_path])
    local_base = '%s/%s/html/' % (build.path, target)
    # Walks through the built doc files and uploads them
    for root, dirs, names in os.walk(local_base):
        for idx, name in enumerate(names):
            with open(os.path.join(root, name), 'rb') as fp:
                file = File(fp)
                dest = '%s/%s' % (dest_base,
                                  os.path.relpath(file.name, local_base))
                logger.info('Uploading %s...' % dest)
                docs_storage.save(dest, file)
                # Invalidates cache
                cache.delete(dest)
                # Deletes the file from local after uploading
                file.close()
                os.remove(os.path.join(root, name))
        count += idx
    shutil.rmtree(build.path)
    # Updates the project's modified date
    project.save()
    build.status = Build.SUCCESS
    build.save()
    logger.info('Finished uploading %s files' % count)
