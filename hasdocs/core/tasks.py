import logging

from celery import task

logger = logging.getLogger(__name__)


@task
def build_docs():
    """Builds new docs using the appropriate autodoc module."""
    pass

@task
def update_docs():
    """Uploads the built docs to the appropriate storage."""
    pass