import base64
import logging
import os

from rauth.service import OAuth2Service

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from hasdocs.accounts.forms import BillingUpdateForm, ConnectionsUpdateForm, \
    OrganizationsUpdateForm, ProfileUpdateForm
from hasdocs.accounts.models import Organization, User
from hasdocs.accounts.tasks import github_api_get, sync_user_account_github, \
    sync_org_account_github
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
    context_object_name = 'account'
    template_name = 'accounts/user_detail.html'

    def get_context_data(self, **kwargs):
        """Returns the context with account and projects for this user."""
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['projects'] = Project.objects.owned_by(
            account=self.object, user=self.request.user)
        if self.request.user.is_owner(self.object):
            context['owner'] = True
        return context

    def get_object(self):
        """Returns the User or Organization object for the given slug."""
        try:
            user = User.objects.get(login=self.kwargs['slug'])
            if user.is_active:
                return user
            else:
                raise Http404
        except User.DoesNotExist:
            return get_object_or_404(Organization, login=self.kwargs['slug'])


class SettingsUpdate(UpdateView):
    """View for updating various settings."""
    success_url = '.'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SettingsUpdate, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

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


def create_user(access_token):
    """Creates a new user based on GitHub's user data."""
    logger.info('Creating a new user based on data from GitHub')
    payload = {'access_token': access_token}
    data = github_api_get('/user', params=payload)
    # Creates a new user based on data from GitHub
    user = User.from_kwargs(github_access_token=access_token, **data)
    # Authenticate and sign in the user
    user = authenticate(access_token=access_token)
    return user


def create_orgs(user):
    """Creates new organization users based on data from GitHub."""
    logger.info('Creating new organization users based on data from GitHub')
    payload = {'access_token': user.github_access_token}
    orgs = github_api_get('/user/orgs', params=payload)
    for org in orgs:
        data = github_api_get('/orgs/%s' % org['login'], params=payload)
        organization = Organization.from_kwargs(**data)
        organization.members.add(user)
        sync_org_account_github(organization, payload)
        logger.info('Organization %s has been created' % organization)


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
    if not request.GET.get('state') and not request.GET.get('code'):
        # Then this is not a proper redirect from GitHub
        raise SuspiciousOperation
    if request.GET['state'] != request.session['state']:
        # Then this is possibily a forgery
        logger.warning('Possible CSRF attack was attempted: %s' % request)
        raise SuspiciousOperation
    data = dict(code=request.GET['code'], state=request.GET['state'])
    logger.info('Requesting access token from GitHub')
    token = github.get_access_token('POST', data=data)
    if token.content.get('error'):
        logger.warning(token.content['error'])
        return HttpResponse('Unknown error occored.')
    user = authenticate(access_token=token.content['access_token'])
    if user is None:
        user = create_user(token.content['access_token'])
        create_orgs(user)
    login(request, user)
    return HttpResponseRedirect(reverse('home'))


def sync_account_github(request):
    """Syncs a user or an organization account with GitHub"""
    if request.method == 'GET':
        raise Http404
    payload = {'access_token': request.user.github_access_token}
    if request.POST.get('organization'):
        logger.info('Syncing organization account %s with GitHub' %
                    request.POST['organization'])
        org = Organization.objects.get(login=request.POST['organization'])
        try:
            sync_org_account_github(org, payload)
            logger.info('Organization %s has been synced' % org)
        except IOError as e:
            messages.error(request, 'GitHub: %s' % e.strerror)
        return HttpResponseRedirect(org.get_absolute_url())
    else:
        logger.info('Syncing user account %s with GitHub' % request.user)
        try:
            sync_user_account_github(request.user, payload)
            logger.info('User account %s has been synced' % request.user)
        except IOError as e:
            messages.error(request, 'GitHub: %s' % e.strerror)
        return HttpResponseRedirect(request.user.get_absolute_url())
