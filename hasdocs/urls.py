from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from hasdocs.accounts.views import BillingUpdate, ConnectionsUpdate, \
    ProfileUpdate, UserDetail
from hasdocs.core.views import ArticleDetail, Contact, Plans
from hasdocs.projects.views import  ProjectBuildDetail, ProjectBuildList, \
    ProjectActivate, ProjectDelete, ProjectDetail, ProjectList, ProjectUpdate

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Home
    url(r'^$', 'hasdocs.core.views.home', name='home'),
    # Admin documentations
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Admin
    #url(r'^admin/', include(admin.site.urls)),

    # Login view
    url(r'^login/$', 'hasdocs.accounts.views.oauth_authenticate',
        name='login'),
    # Logout view
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # Profile settings
    url(r'^settings/profile/$', ProfileUpdate.as_view(),
        name='profile_settings'),
    # Billing settings
    url(r'^settings/billing/$', BillingUpdate.as_view(),
        name='billing_settings'),
    # Connections settings
    url(r'^settings/connections/$', ConnectionsUpdate.as_view(),
        name='connections_settings'),

    # OAuth
    url(r'^oauth2/$', 'hasdocs.accounts.views.oauth_authenticate',
        name='oauth_authenticate'),
    url(r'^oauth2/authenticated/$',
        'hasdocs.accounts.views.oauth_authenticated',
        name='oauth_authenticated'),

    # Explore
    url(r'^explore/$', ProjectList.as_view(), name='explore'),
    # How it works
    url(r'^how/$', TemplateView.as_view(template_name='content/how.html'),
        name='how'),
    # Pricing
    url(r'^pricing/$', Plans.as_view(), name='pricing'),
    # Help
    url(r'^help/$', TemplateView.as_view(template_name='content/help.html'),
        name='help'),
    # Contact form
    url(r'^contact/$', Contact.as_view(), name='contact'),
    # Thanks
    url(r'^thanks/$', TemplateView.as_view(
        template_name='content/thanks.html'), name='thanks'),
    # Terms of service
    url(r'^terms/$', TemplateView.as_view(template_name='content/terms.html'),
        name='terms'),
    # Privacy policy
    url(r'^privacy/$',
        TemplateView.as_view(template_name='content/privacy.html'),
        name='privacy'),
    
    # Articles
    url(r'^articles/(?P<title>[\w-]+)/$', ArticleDetail.as_view(),
        name='article_detail'),

    # GitHub post-receive hook
    url(r'^post-receive/github/$', 'hasdocs.core.views.post_receive_github',
        name='github_hook'),
    # Heroku http deploy hook
    url(r'^post-receive/heroku/$', 'hasdocs.core.views.post_receive_heroku',
        name='heroku_hook'),
    # Restart build
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/builds/restart/$',
        'hasdocs.core.views.restart_build', name='restart_build'),

    # Sync user's repositories with GitHub
    url(r'^sync/github/$', 'hasdocs.accounts.views.sync_account_github',
        name='sync_account_github'),

    # Import from a Heroku project
    url(r'^heroku/import/$', 'hasdocs.projects.views.import_from_heroku',
        name='import_from_heroku'),

    # Account detail
    #url(r'^(?P<slug>[\w-]+)/$', AccountDetail.as_view(), name='account_detail'),
    # User detail
    url(r'^(?P<slug>[\w-]+)/$', UserDetail.as_view(), name='user_detail'),
    # Project detail
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/$',
        ProjectDetail.as_view(), name='project_detail'),
    # Project activate
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/activate/$',
        ProjectActivate.as_view(), name='project_activate'),
    # Project update
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/edit/$',
        ProjectUpdate.as_view(), name='project_update'),
    # Project delete
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/delete/$',
        ProjectDelete.as_view(), name='project_delete'),
    # List of builds for a project
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/builds/$',
        ProjectBuildList.as_view(), name='project_build_list'),
    # Build detail
    url(r'^(?P<username>[\w-]+)/(?P<project>[\w.-]+)/builds/(?P<pk>\d+)/$',
        ProjectBuildDetail.as_view(), name='project_build_detail'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
