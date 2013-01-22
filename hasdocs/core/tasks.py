import os
import shutil
import subprocess
import tarfile

import celery
import pusher
import requests
from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.core.cache import cache
from django.core.files import File

from hasdocs.projects.models import Build

logger = celery.utils.log.get_task_logger(__name__)

docs_storage = S3BotoStorage(
    bucket=settings.AWS_DOCS_BUCKET_NAME, acl='private',
    reduced_redundancy=True, secure_urls=False
)

pusher = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_API_KEY, secret=settings.PUSHER_API_SECRET
)


def update_docs(project):
    """Fetches the source repo, builds docs and uploads them for serving."""
    build = Build.objects.create(project=project, status=Build.UNKNOWN)
    logger.info('Build %s started' % build)
    celery.chain(
        fetch_source.s(build, project),
        extract.s(project),
        build_docs.s(project),
        upload_docs.s(project)
    ).apply_async()
    return build


@celery.task
def fetch_source(build, project):
    """Fetchs the source from a GitHub repository."""
    logger.info('Fetching source for %s from GitHub' % project)
    if project.owner.is_organization():
        access_token = project.owner.organization.team_set.get(
            name='Owners'
        ).members.exclude(github_access_token='')[0].github_access_token
    else:
        access_token = project.owner.user.github_access_token
    payload = {'access_token': access_token}
    r = requests.get('%s/repos/%s/%s/tarball' % (
        settings.GITHUB_API_URL, project.owner, project.name,
    ), params=payload)
    build.filename = '%s.tar.gz' % project
    with open(build.filename, 'wb') as file:
        file.write(r.content)
    return build


@celery.task
def extract(build, project):
    """Extracts the given tarball and returns its resulting path."""
    logger.debug('Extracting %s', build.filename)
    try:
        with tarfile.open(build.filename) as tar:
            build.path = tar.next().path
            tar.extractall()
        return build
    except tarfile.ReadError:
        logger.warning('Error opening file %s' % build.filename)
        raise
    finally:
        os.remove(build.filename)


@celery.task
def fetch_virtualenv(build, project):
    """etrives the virtualenv for the project from S3, if any."""
    logger.info('Fetching virtualenv for %s/%s' % (
        project.owner, project.name))
    source = '%s/%s/%s' % (project.owner, project.name, settings.VENV_FILENAME)
    try:
        with docs_storage.open(source, 'r') as fp:
            with tarfile.open(fileobj=fp) as tar:
                tar.extractall()
            logger.info('Fetched previously stored virtualenv')
    except IOError:
        logger.info('No previously stored virtualenv was found')
    finally:
        return build


@celery.task
def build_docs(build, project):
    """Builds the documentations for the projects."""
    logger.info('Building documentation for %s/%s' % (
        project.owner, project.name))
    args = ['bash']
    if project.generator.name == 'Sphinx':
        args += ['bin/build_sphinx', build.path, project.docs_path,
                 project.requirements_path]
    elif project.generator.name == 'Jekyll':
        args += ['bin/build_jekyll', build.path, project.docs_path]
    try:
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True)
        # Poll until the process terminates
        while proc.poll() is None:
            line = proc.stdout.readline()
            if line:
                build.output += line
                channel = 'build-%s' % build.pk
                pusher[channel].trigger('log', {'message': line})
        build.save()
        logger.info('Built docs for %s/%s' % (project.owner, project.name))
        return build
    except subprocess.CalledProcessError, e:
        logger.warning('Build failed for %s/%s' % (
            project.owner, project.name))
        build.output = e.output
        build.status = Build.FAILURE
        build.save()
        # TODO: nicer cleanup of mess on failure (maybe an error link)
        shutil.rmtree(build.path)
        # TODO: nicer handling of exception
        raise


@celery.task
def store_virtualenv(build, project):
    """Stores the virtualenv in S3 for future builds."""
    logger.info('Storing virtualenv for %s/%s' % (project.owner, project.name))
    venv = '%s/%s' % (build.path, settings.VENV_FILENAME)
    dest = '%s/%s/%s' % (project.owner, project.name, settings.VENV_FILENAME)
    with tarfile.open(venv, 'w:gz') as tar:
        tar.add('%s/%s' % (build.path, settings.VENV_NAME))
    with open(venv, 'rb') as fp:
        file = File(fp)
        docs_storage.save(dest, file)
    os.remove(venv)
    logger.info('Stored virtualenv for %s/%s' % (project.owner, project.name))
    return build


@celery.task
def upload_docs(build, project):
    """Uploads the built docs to the appropriate storage."""
    project = build.project
    logger.info('Uploading docs for %s' % project)
    count = 0
    dest_base = '%s/%s' % (project.owner, project.name)
    if project.generator.name == 'Sphinx':
        target = subprocess.check_output(
            ['bash', 'bin/target_sphinx', build.path, project.docs_path])
    elif project.generator.name == 'Jekyll':
        target = subprocess.check_output(
            ['bash', 'bin/target_jekyll', build.path, project.docs_path])
    local_base = '%s/%s/' % (build.path, target.rstrip())
    # Walks through the built doc files and uploads them
    for root, dirs, names in os.walk(local_base):
        for idx, name in enumerate(names):
            with open(os.path.join(root, name), 'rb') as fp:
                file = File(fp)
                dest = '/%s/%s' % (dest_base,
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
