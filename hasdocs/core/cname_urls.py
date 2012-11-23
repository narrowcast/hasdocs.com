from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # User or project page with custom domain
    url(r'^$', 'hasdocs.core.views.custom_domain_page', name='custom_domain_page'),
    # Static documentation files
    url(r'^(?P<path>.*)$', 'hasdocs.core.views.serve_static_cname', name='serve_static_cname'),
)