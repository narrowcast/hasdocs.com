from django.conf import settings
from django.contrib.sites.models import Site
from django.http import Http404

from hasdocs.projects.models import Domain, Project

class SubdomainMiddleware:
    """Middleware for handling subdomains."""
    def process_request(self, request):
        host = request.get_host()
        subdomain = host.split('.')[0]
        request.slug = None
        request.subdomain = subdomain
        print host
        print subdomain
        print Site.objects.get_current().domain
        if subdomain != 'www':
            # Then handle subdomain urls
            request.urlconf = settings.SUBDOMAIN_URLCONF
        # Handle custom domains
        if Site.objects.get_current().domain not in host:
            try:
                # WTF redis or similar for cname lookup may speed up things
                domain = Domain.objects.get(name=host)
                project = Project.objects.get(custom_domains=domain)
                # WTF this part is somewhat ghetto, need to clean up
                request.subdomain = project.owner
                request.slug = project
                request.urlconf = settings.SUBDOMAIN_URLCONF
            except Domain.DoesNotExist:
                # Then CNAME points to our domain, but no record on our side
                raise Http404