import base64
import logging
import os
import requests
from rauth.service import OAuth2Service

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView

from hasdocs.accounts.forms import SignupForm, UserUpdateForm

logger = logging.getLogger(__name__)

# GitHub OAuth 2.0 client
github = OAuth2Service(
    name='GitHub',
    consumer_key=settings.GITHUB_CLIENT_ID,
    consumer_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url=settings.GITHUB_ACCESS_TOKEN_URL,
    authorize_url=settings.GITHUB_AUTHORIZE_URL
)


class UserCreateView(CreateView):
    """View for creating a user."""
    model = User
    form_class = SignupForm

class UserDetailView(DetailView):
    """View for showing user detail."""
    model = User
    slug_field = 'username'
    context_object_name = 'account'
    template_name='accounts/user_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        # Retrieves the list of GitHub repos
        access_token = self.request.user.get_profile().github_access_token
        payload = {'access_token': access_token }
        r = requests.get('%s/user/repos' % settings.GITHUB_API_URL,
                         params=payload)
        context['repos'] = r.json
        # Retrieves the list of Heroku apps
        headers = {'Accept': 'application/json'}
        r = requests.get('%s/apps' % settings.HEROKU_API_URL, headers=headers,
                     auth=('', self.request.user.get_profile().heroku_api_key))
        context['apps'] = r.json
        return context
        
class UserUpdateView(UpdateView):
    """View for updating user settings."""
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = "."
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserUpdateView, self).dispatch(*args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _("Thanks, your settings have been saved."))
        return super(UserUpdateView, self).form_valid(form)

def oauth_authenticate(request):
    """Request authorization usnig OAuth2 protocol."""
    request.session['state'] = base64.b64encode(os.urandom(40))
    # the return URL is used to validate the request
    url = github.get_authorize_url(state=request.session['state'])
    logger.debug('authorize_url: %s' % url)
    return HttpResponseRedirect(url)

def oauth_authenticated(request):
    """Callback to be called after authorization from GitHub."""
    if request.GET['state'] != request.session['state']:
        # Then this is possibily a forgery
        logger.warning('Possible CSRF attack was attempted.' % url)
        return HttpResponse('You may be a victim of CSRF attack.')
    data = dict(code = request.GET['code'], state = request.GET['state'])
    token = github.get_access_token('POST', data=data)
    
    if token.content.get('error'):
        logger.debug(token.content['error'])
    # Stores the access token in user profile
    profile = request.user.get_profile()
    profile.github_access_token = token.content['access_token']
    profile.save()
    return HttpResponseRedirect(reverse('settings'))