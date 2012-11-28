from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from hasdocs.accounts.views import (BillingUpdateView, ConnectionsUpdateView,
    OrganizationsUpdateView, ProfileUpdateView, UserCreateView)
from hasdocs.core.views import ContactView, PlansView
from hasdocs.projects.views import (
    GitHubProjectListView, HerokuProjectListView, ProjectDetailView,
    ProjectDeleteView, ProjectListView, ProjectUpdateView
)

admin.autodiscover()

urlpatterns = patterns('',
    # Home
    url(r'^$', 'hasdocs.core.views.home', name='home'),
    # Admin documentations
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Admin
    url(r'^admin/', include(admin.site.urls)),
    
    # Login view
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    # Logout view
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # Signup
    url(r'^signup/$', UserCreateView.as_view(), name='signup'),

    # Profile settings
    url(r'^settings/profile/$', ProfileUpdateView.as_view(), name='profile_settings'),
    # Billing settings
    url(r'^settings/billing/$', BillingUpdateView.as_view(), name='billing_settings'),
    # Connections settings
    url(r'^settings/connections/$', ConnectionsUpdateView.as_view(), name='connections_settings'),
    # Organizations settings
    url(r'^settings/organizations/$', OrganizationsUpdateView.as_view(), name='organizations_settings'),

    # OAuth
    url(r'^oauth2/$', 'hasdocs.accounts.views.oauth_authenticate', name='oauth_authenticate'),
    url(r'^oauth2/authenticated/$', 'hasdocs.accounts.views.oauth_authenticated', name='oauth_authenticated'),

    # Explore
    url(r'^explore/$', ProjectListView.as_view(), name='explore'),
    # How it works
    url(r'^how/$', TemplateView.as_view(template_name='content/how.html'), name='how'),
    # Pricing
    url(r'^pricing/$', PlansView.as_view(), name='pricing'),
    # Help
    url(r'^help/$', TemplateView.as_view(template_name='content/help.html'), name='help'),
    # Contact form
    url(r'^contact/$', ContactView.as_view(), name='contact'),
    # Terms of service
    url(r'^terms/$', TemplateView.as_view(template_name='content/terms.html'), name='terms'),
    # Privacy policy
    url(r'^privacy/$', TemplateView.as_view(template_name='content/privacy.html'), name='privacy'),    
 
    # GitHub post-receive hook
    url(r'^post-receive/github/$', 'hasdocs.core.views.post_receive_github', name='github_hook'),
    # Heroku http deploy hook
    url(r'^post-receive/heroku/$', 'hasdocs.core.views.post_receive_heroku', name='heroku_hook'),
    
    # List of GitHub repositories
    url(r'^github/$', GitHubProjectListView.as_view(), name='project_list_github'),
    # List of Heroku apps
    url(r'^heroku/$', HerokuProjectListView.as_view(), name='project_list_heroku'),
    
    # Import from a GitHub project
    url(r'^github/import/$',
        'hasdocs.projects.views.import_from_github',name='import_from_github'),
    # Import from a Heroku project
    url(r'^heroku/import/$',
        'hasdocs.projects.views.import_from_heroku', name='import_from_heroku'),
    
    # User detail
    url(r'^(?P<slug>[\w.-]+)/$', 'hasdocs.core.views.user_detail', name='user_detail'),
    # Project detail
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/$', ProjectDetailView.as_view(), name='project_detail'),
    # Project update
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/edit/$', ProjectUpdateView.as_view(), name='project_update'),
    # Project delete
    url(r'^(?P<username>\w+)/(?P<slug>[\w.-]+)/delete/$', ProjectDeleteView.as_view(), name='project_delete'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()