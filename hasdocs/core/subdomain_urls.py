from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # User page
    url(r'^$', 'hasdocs.core.views.user_page', name='user_page'),
    # Project page
    url(r'^(?P<slug>[\w.-]+)/$', 'hasdocs.core.views.project_page', name='project_page'),
    # Static documentation files
    url(r'^(?P<slug>[\w.-]+)/(?P<path>.*)$', 'hasdocs.core.views.serve_static', name='serve_static'),
)