from django.conf.urls import patterns, url

from hasdocs.projects.views import ProjectDocs

urlpatterns = patterns(
    '',
    # User page
    url(r'^$', 'hasdocs.core.views.user_page', name='user_page'),
    # Project page
    url(r'^(?P<project>[\w\.-]+)/$', ProjectDocs.as_view(),
        name='project_docs'),
    # Static documentation files
    url(r'^(?P<project>[\w\.-]+)/(?P<path>.*)$', 'hasdocs.core.views.serve',
        name='serve'),
)
