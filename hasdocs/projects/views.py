import json
import logging
import requests

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from hasdocs.core.tasks import update_docs
from hasdocs.projects.forms import ProjectCreateForm
from hasdocs.projects.models import Generator, Language, Project

logger = logging.getLogger(__name__)


class OwnershipRequiredMixin(object):    
    """Mixin for requiring membership to access the project."""

    def has_ownership(user, project):
        """Returns whether the user has ownership for the project."""
        access_token = user.get_profile().github_access_token
        payload = {'access_token': access_token}
        r = requests.get('%s/orgs/%s/teams' % (
            settings.GITHUB_API_URL, project.owner), params=payload)
        if r.ok:
            teams = r.json
            ids = [team['id'] for team in teams if team['name'] == 'Owners']
            r = requests.get('%s/teams/%s/members/%s' % (
                settings.GITHUB_API_URL, ids[0], user.username),
                params=payload)
            return r.status_code == 204
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        """Limits access to the owners of the project."""
        project = get_object_or_404(Project, name=kwargs['slug'])
        if project.owner.get_profile().user_type.name == 'Organization':
            # Then checks if the user is owner of the project's organization
            if not has_ownership(request.user, project):
                raise Http404
        else:
            # Then check if the user is owner of the project
            if request.user != project.owner:
                raise Http404
        return super(OwnershipRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class MembershipRequiredMixin(object):
    """Mixin for requiring membership to access the project."""

    def has_membership(user, project):
        """Returns whether the user has membership for the project."""
        access_token = user.get_profile().github_access_token
        payload = {'access_token': access_token, 'type': 'member'}
        r = requests.get('%s/orgs/%s/repos' % (
            settings.GITHUB_API_URL, project.owner), params=payload)
        repos = r.json
        # Returns true if project is in the list of repos that user is a member
        return [True for repo in repos if repos['name'] == project.name]

    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name=kwargs['slug'])
        if project.private:
            if project.owner.get_profile().user_type.name == 'Organization':
                # Then checks if the user is member of the project
                if not has_membership(request.user, project):
                    raise Http404
            else:
                # Then checks if the user is owner of the project
                if request.user != project.owner:
                    raise Http404
        return super(MembershipRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class ProjectList(ListView):
    """View for viewing the list of projects in explore page."""
    def get_queryset(self):
        """Limits the list to public projects."""
        return Project.objects.filter(private=False)


class ProjectCreate(CreateView):
    """View for creating a new project."""
    form_class = ProjectCreateForm
    template_name = 'projects/project_create_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Limits access to the requesting user."""
        if kwargs['username'] != request.user.username:
            raise Http404
        return super(ProjectCreate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Imports the repository from GitHub and redirects to the project."""
        project = form.save()
        import_from_github(self.request, project)
        project.save()
        return HttpResponseRedirect(
            reverse('project_detail', args=[project.owner, project.name]))

    def get_context_data(self, **kwargs):
        """Returns the context with project name."""
        context = super(ProjectCreate, self).get_context_data(**kwargs)
        context['project'] = self.kwargs['slug']
        return context

    def get_initial(self):
        """Returns the initial data for the form."""
        initial = super(ProjectCreate, self).get_initial()
        initial['owner'] = self.request.user
        initial['name'] = self.kwargs['slug']
        return initial


class ProjectDetail(MembershipRequiredMixin, DetailView):
    """View for showing the project details."""
    model = Project
    slug_field = 'name'
    context_object_name = 'project'


class ProjectUpdate(OwnershipRequiredMixin, UpdateView):
    """View for updating project details."""
    model = Project
    slug_field = 'name'

    def form_valid(self, form):
        """Logs updating of the project."""
        logger.info('Updated project %s' % self.kwargs['slug'])
        return super(ProjectUpdate, self).form_valid(form)


class ProjectDelete(OwnershipRequiredMixin, DeleteView):
    """View for delting a project."""
    model = Project
    slug_field = 'name'

    def get_success_url(self):
        """Returns the URL of the user's detail_view."""
        logger.info('Deleted project %s' % self.kwargs['slug'])
        return self.request.user.get_absolute_url()


class ProjectLogs(MembershipRequiredMixin, DetailView):
    """View for viewing the logs for a project."""
    model = Project
    slug_field = 'name'
    template_name = 'projects/project_logs.html'


class GitHubProjectList(TemplateView):
    """View for viewing the list of GitHub projects."""
    template_name = 'projects/project_list_github.html'

    def dispatch(self, request, *args, **kwargs):
        """Checks whether user has GitHub access token and redirects if not."""
        access_token = request.user.get_profile().github_access_token
        if not access_token:
            # Then redirect to GitHub OAuth view
            return HttpResponseRedirect(reverse('oauth_authenticate'))
        return super(GitHubProjectList, self).dispatch(
            request, args, **kwargs)

    def get_context_data(self, **kwargs):
        """Sets the list of GitHub repositories as context."""
        context = super(GitHubProjectList, self).get_context_data(**kwargs)
        access_token = self.request.user.get_profile().github_access_token
        payload = {'access_token': access_token}
        r = requests.get('%s/user/repos' % settings.GITHUB_API_URL,
                         params=payload)
        repos = r.json
        # Mark already imported repos
        for repo in repos:
            repo['exists'] = Project.objects.filter(
                url=repo['html_url']).exists()
        context['repos'] = repos
        context['form'] = ProjectCreateForm()
        return context


class HerokuProjectList(TemplateView):
    """View for viewing the list of Heroku projects."""
    template_name = 'projects/project_list_heroku.html'

    def dispatch(self, request, *args, **kwargs):
        """Checks whether user has Heroku api key and redirects if not."""
        api_key = request.user.get_profile().heroku_api_key
        if not api_key:
            # Then redirect to Heroku OAuth view
            pass
        return super(HerokuProjectList, self).dispatch(
            request, args, **kwargs)

    def get_context_data(self, **kwargs):
        """Sets the list of Heroku apps as context."""
        context = super(HerokuProjectList, self).get_context_data(**kwargs)
        api_key = self.request.user.get_profile().heroku_api_key
        r = requests.get('%s/apps' % settings.HEROKU_API_URL,
                         auth=('', api_key))
        apps = r.json
        # Mark already imported apps
        for app in apps:
            app['exists'] = Project.objects.filter(url=app['web_url']).exists()
        context['apps'] = apps
        return context


def import_from_github(request, project):
    """Imports a project from a GitHub repository."""
    logger.info('Importing a repository from GitHub')
    access_token = project.owner.get_profile().github_access_token
    payload = {'access_token': access_token}
    r = requests.get('%s/repos/%s/%s' % (
        settings.GITHUB_API_URL, project.owner.username, project.name
    ), params=payload)
    repo = r.json
    project.description = repo['description']
    project.url = repo['html_url']
    project.git_url = repo['git_url']
    project.private = repo['private']
    logger.info('Imported %s repo from GitHub' % project.name)
    # Creates a post-receive webhook at GitHub
    create_hook_github(request, project)
    # Build docs for the first time
    update_docs.delay(project)


def import_from_heroku(request):
    """Imports a project from a Heroku app."""
    if request.method == 'POST':
        logger.info('Importing an app from Heroku')
        api_key = request.user.get_profile().heroku_api_key
        r = requests.get('%s/apps/%s' % (
            settings.HEROKU_API_URL, request.POST['app_name']
        ), auth=('', api_key))
        app = r.json
        # Creates a new project based on the Heroku app
        language = Language.objects.get(
            name=app['buildpack_provided_description'])
        # TODO: generator must be detected from project data
        generator = Generator.objects.get(name='Sphinx')
        project = Project(owner=request.user, name=app['name'],
                          url=app['web_url'], git_url=app['git_url'],
                          private=True, language=language, generator=generator)
        project.save()
        logger.info('Imported %s app from Heroku.' % project.name)
        # Creates a post-receive webhook at GitHub
        create_hook_heroku(request)
        # Build docs for the first time
        update_docs.delay(project)
        return HttpResponseRedirect(
            reverse('project_detail', args=[request.user, project]))
    else:
        raise Http404


def create_hook_github(request, project):
    """Creates a post-receive hook for the given project at the GitHub repo."""
    logger.info('Creating a post-receive hook at GitHub')
    access_token = project.owner.get_profile().github_access_token
    url = request.build_absolute_uri(reverse('github_hook'))
    config = {'url': url}
    payload = {'name': 'web', 'config': config}
    r = requests.post('%s/repos/%s/%s/hooks' % (
        settings.GITHUB_API_URL, project.owner.username, project.name
    ), data=json.dumps(payload), params={'access_token': access_token})
    logger.info('Received %s from GitHub for %s' % (r, project.name))
    return r


def create_hook_heroku(request):
    """Creates a post-receive hook for the given project at the Heroku repo."""
    logger.info('Creating a post-receive hook at Heroku')
    api_key = request.user.get_profile().heroku_api_key
    url = request.build_absolute_uri(reverse('heroku_hook'))
    headers = {'Accept': 'application/json'}
    r = requests.post('%s/apps/%s/addons/deployhooks:http' % (
        settings.HEROKU_API_URL, request.POST['app_name']
    ), data=({'config[url]': url}), auth=('', api_key), headers=headers)
    logger.info('Received %s from Heroku for %s' % (
        r, request.POST['app_name']))
    return r
