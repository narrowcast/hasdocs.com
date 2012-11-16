from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin

from hasdocs.accounts.views import UserCreateView, UserUpdateView
from hasdocs.core.views import ContactView
from hasdocs.projects.views import ProjectDetailView, ProjectListView, ProjectUpdateView

admin.autodiscover()

urlpatterns = patterns('',
    # Home
    url(r'^$', 'hasdocs.core.views.home', name='home'),    
    # Admin
    url(r'^admin/', include(admin.site.urls)),
    
    # Login view
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    # Logout view
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # Signup
    url(r'^signup/$', UserCreateView.as_view(), name='signup'),

    # User settings
    url(r'^settings/$', UserUpdateView.as_view(), name='settings'),

    # OAuth
    url(r'^oauth2/$', 'hasdocs.accounts.views.oauth_authenticate', name='oauth_authenticate'),
    url(r'^oauth2/authenticated/$', 'hasdocs.accounts.views.oauth_authenticated', name='oauth_authenticated'),

    # Explore
    url(r'^explore/$', ProjectListView.as_view(), name='explore'),
    # How it works
    url(r'^how/$', TemplateView.as_view(template_name="content/how.html"), name='how'),
    # Pricing
    url(r'^pricing/$', TemplateView.as_view(template_name="content/pricing.html"), name='pricing'),
    # Terms of service
    url(r'^terms/$', TemplateView.as_view(template_name="content/terms.html"), name='terms'),
    # Privacy policy
    url(r'^privacy/$', TemplateView.as_view(template_name="content/privacy.html"), name='privacy'),
    # Contact form
    url(r'^contact/$', ContactView.as_view(), name='contact'),
 
    # GitHub post-receive hook
    url(r'^post-receive/github/$', 'hasdocs.core.views.post_receive_github', name='github'),
    # Heroku deploy hook
    url(r'^post-receive/heroku/$', 'hasdocs.core.views.post_receive_heroku', name='heroku'),
    
    # User detail or project page if subdomain is set
    url(r'^(?P<slug>\w+)/$', 'hasdocs.core.views.user_or_page', name='user_or_page'),
    # Project detail
    url(r'^(?P<username>\w+)/(?P<slug>\w+)/$', ProjectDetailView.as_view(), name='project_detail'),
    # Project edit
    url(r'^(?P<username>\w+)/(?P<slug>\w+)/edit/$', ProjectUpdateView.as_view(), name='project_update'),
)