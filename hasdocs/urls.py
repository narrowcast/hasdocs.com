from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from hasdocs.accounts.views import BillingUpdate, ConnectionsUpdate, \
    OrganizationsUpdate, ProfileUpdate, UserDetail
from hasdocs.core.views import Contact, Plans
from hasdocs.projects.views import GitHubProjectList, HerokuProjectList, \
    ProjectCreate, ProjectDetail, ProjectDelete, ProjectList, ProjectLogs, \
    ProjectUpdate

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Home
    url(r'^$', 'hasdocs.core.views.home', name='home'),
    # Admin documentations
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # Login view
    #url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
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
    # Organizations settings
    url(r'^settings/organizations/$', OrganizationsUpdate.as_view(),
        name='organizations_settings'),

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
    # Terms of service
    url(r'^terms/$', TemplateView.as_view(template_name='content/terms.html'),
        name='terms'),
    # Privacy policy
    url(r'^privacy/$',
        TemplateView.as_view(template_name='content/privacy.html'),
        name='privacy'),
    
    # Articles
    url(r'^articles/(?P<title>[\w-]+)/$', 'hasdocs.core.views.article_detail',
        name='article_detail'),

    # GitHub post-receive hook
    url(r'^post-receive/github/$', 'hasdocs.core.views.post_receive_github',
        name='github_hook'),
    # Heroku http deploy hook
    url(r'^post-receive/heroku/$', 'hasdocs.core.views.post_receive_heroku',
        name='heroku_hook'),

    # List of GitHub repositories
    url(r'^github/$', GitHubProjectList.as_view(),
        name='project_list_github'),
    # List of Heroku apps
    url(r'^heroku/$', HerokuProjectList.as_view(),
        name='project_list_heroku'),

    # Import from a Heroku project
    url(r'^heroku/import/$', 'hasdocs.projects.views.import_from_heroku',
        name='import_from_heroku'),

    # User detail
    url(r'^(?P<slug>[\w.-]+)/$', UserDetail.as_view(), name='user_detail'),
    # Project detail
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/$', ProjectDetail.as_view(),
        name='project_detail'),
    # Project logs
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/logs/$',
        ProjectLogs.as_view(), name='project_logs'),
    # Project create
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/create/$',
        ProjectCreate.as_view(), name='project_create'),
    # Project update
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/edit/$',
        ProjectUpdate.as_view(), name='project_update'),
    # Project delete
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/delete/$',
        ProjectDelete.as_view(), name='project_delete'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
