class SubdomainMiddleware:
    """Middleware for handling subdomains."""
    def process_request(self, request):
        host = request.META.get('HTTP_HOST')
        request.subdomain = host.split('.')
        print host
        print request.subdomain