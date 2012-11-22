from django.http import Http404

from hasdocs.projects.models import Domain, Project

class SubdomainMiddleware:
    """Middleware for handling subdomains."""
    def process_request(self, request):
        host = request.get_host()
        subdomain = host.split('.')[0]
        if subdomain == 'www':
            request.subdomain = None
        else:
            request.subdomain = subdomain
            request.urlconf = 'hasdocs.core.urls'
        # Handle custom domains
        if 'test.com' not in host:
            try:
                domain = Domain.objects.get(name=host)
                project = Project.objects.get(custom_domains=domain)
                #request.subdomain = project.owner
                #request.slug = project
            except Domain.DoesNotExist:
                # Then CNAME points to our domain, but no record on our side
                raise Http404