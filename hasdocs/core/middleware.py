class SubdomainMiddleware:
    """Middleware for handling subdomains."""
    def process_request(self, request):
        host = request.META.get('HTTP_HOST')
        subdomain = host.split('.')[0]
        if subdomain == 'www':
            request.subdomain = None
        else:
            request.subdomain = subdomain