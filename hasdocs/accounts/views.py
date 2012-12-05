import base64
import logging
import os
import re

import requests
from rauth.service import OAuth2Service

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from hasdocs.accounts.forms import BillingUpdateForm, ConnectionsUpdateForm
from hasdocs.accounts.forms import OrganizationsUpdateForm, ProfileUpdateForm
from hasdocs.accounts.models import UserProfile, UserType
from hasdocs.projects.models import Project

logger = logging.getLogger(__name__)

# GitHub OAuth 2.0 client
github = OAuth2Service(
    name='GitHub',
    consumer_key=settings.GITHUB_CLIENT_ID,
    consumer_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url=settings.GITHUB_ACCESS_TOKEN_URL,
    authorize_url=settings.GITHUB_AUTHORIZE_URL
)


class UserDetail(DetailView):
    """View for showing user detail."""
    model = User
    slug_field = 'username'
    context_object_name = 'account'
    template_name = 'accounts/user_detail.html'

    def get_context_data(self, **kwargs):
        """Returns the context with account and projects for this user."""
        context = super(UserDetail, self).get_context_data(**kwargs)
        user = kwargs['object']
        projects = Project.objects.filter(owner=user)
        if user != self.request.user:
            # Then limit access to the public projects
            projects = projects.filter(private=False)
        context['account'] = user
        context['projects'] = projects
        return context


class SettingsUpdate(UpdateView):
    """View for updating various settings."""
    success_url = '.'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SettingsUpdate, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def form_valid(self, form):
        messages.success(self.request,
                         _("Thanks, your settings have been saved."))
        return super(SettingsUpdate, self).form_valid(form)


class ProfileUpdate(SettingsUpdate):
    """View for updating profile settings."""
    form_class = ProfileUpdateForm


class BillingUpdate(SettingsUpdate):
    form_class = BillingUpdateForm


class ConnectionsUpdate(SettingsUpdate):
    """View for updating connections settings."""
    form_class = ConnectionsUpdateForm


class OrganizationsUpdate(SettingsUpdate):
    """View for updating organizations settings."""
    form_class = OrganizationsUpdateForm


def create_orgs(access_token):
    """Creates new organization users based on data from GitHub."""
    logger.info('Creating new organization users based on data from GitHub')
    payload = {'access_token': access_token}
    r = requests.get('%s/user/orgs' % settings.GITHUB_API_URL, params=payload)
    orgs = r.json
    for org in orgs:
        r = requests.get('%s/orgs/%s' % (
            settings.GITHUB_API_URL, org['login']), params=payload)
        data = r.json
        try:
            user = User.objects.get(username=data['login'])
            profile = user.get_profile()
        except User.DoesNotExist:
            user = User.objects.create_user(data['login'], data['email'])
            profile = UserProfile.objects.create(user=user)
        user.first_name = data['name']
        user.user_type = UserType.objects.get(name='Organization')
        user.save()
        # Update profile based on data from GitHub
        if data['avatar_url']:
            match = re.match('.+/avatar/(?P<hashcode>\w+)?.+',
                             data['avatar_url'])
            profile.gravatar_id = match.group('hashcode')
        profile.url = data['blog'] or ''
        profile.company = data['company'] or ''
        profile.location = data['location'] or ''
        profile.save()


def create_user(access_token):
    """Creates a new user based on GitHub's user data."""
    logger.info('Creating a new user based on data from GitHub')
    payload = {'access_token': access_token}
    r = requests.get('%s/user' % settings.GITHUB_API_URL, params=payload)
    data = r.json
    try:
        user = User.objects.get(username=data['login'])
        profile = user.get_profile()
    except User.DoesNotExist:
        user = User.objects.create_user(data['login'], data['email'])
        profile = UserProfile.objects.create(user=user)
    user.first_name = data['name']
    user.user_type = UserType.objects.get(name='User')
    user.save()
    # Update profile based on data from GitHub
    profile.gravatar_id = data['gravatar_id'] or ''
    profile.url = data['blog'] or ''
    profile.company = data['company'] or ''
    profile.location = data['location'] or ''
    profile.github_access_token = access_token
    profile.save()
    # Authenticate and sign in the user
    user = authenticate(access_token=access_token)
    return user


def oauth_authenticate(request):
    """Request authorization usnig OAuth2 protocol."""
    state = base64.b64encode(os.urandom(40))
    request.session['state'] = state
    logger.info('Redirecting to GitHub for authentication: %s' % state)
    # the return URL is used to validate the request
    url = github.get_authorize_url(state=state, scope='repo')
    return HttpResponseRedirect(url)


def oauth_authenticated(request):
    """Callback to be called after authorization from GitHub."""
    logger.info('Received redirect from GitHub: %s' % request.GET['state'])
    if request.GET['state'] != request.session['state']:
        # Then this is possibily a forgery
        logger.warning('Possible CSRF attack was attempted: %s' % request)
        return HttpResponse('You may be a victim of CSRF attack.')
    data = dict(code=request.GET['code'], state=request.GET['state'])
    logger.info('Requesting access token from GitHub')
    token = github.get_access_token('POST', data=data)
    if token.content.get('error'):
        logger.warning(token.content['error'])
        return HttpResponse('Unknown error occored.')
    user = authenticate(access_token=token.content['access_token'])
    if user is None:
        user = create_user(token.content['access_token'])
    login(request, user)
    return HttpResponseRedirect(reverse('home'))
