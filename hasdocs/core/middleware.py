import logging

from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


class SubdomainMiddleware:
    """Middleware for handling subdomains."""
    def process_request(self, request):
        host = request.get_host()
        subdomain = host.split('.')[0]
        request.subdomain = subdomain
        if subdomain != 'www':
            # Then handle subdomain urls
            request.urlconf = settings.SUBDOMAIN_URLCONF
        # Handle custom domains
        if Site.objects.get_current().domain not in host:
            logger.info('Handling cnamed request from %s' % host)
            request.urlconf = settings.CNAME_URLCONF
