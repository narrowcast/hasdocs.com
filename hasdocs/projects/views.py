import json
import logging
import requests

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, View
from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic.list import ListView

from hasdocs.accounts.mixins import PermissionRequiredMixin
from hasdocs.core.tasks import update_docs
from hasdocs.core.views import serve
from hasdocs.projects.forms import ProjectActivateForm
from hasdocs.projects.models import Build, Generator, Language, Project

logger = logging.getLogger(__name__)


class ProjectList(ListView):
    """View for viewing the list of projects in explore page."""

    def get_queryset(self):
        """Limits the list to public projects."""
        return Project.objects.filter(private=False)


class ProjectMixin(object):
    """Mixin for class-based generic views dealing with a project object."""
    def get_object(self):
        """Returns the project for the given url."""
        return get_object_or_404(
            Project, owner__login=self.kwargs['username'],
            name=self.kwargs['project'])


class ProjectActivate(PermissionRequiredMixin, ProjectMixin, UpdateView):
    """View for creating a service hook for the project."""
    form_class = ProjectActivateForm
    template_name = 'projects/project_activate_form.html'
    required_permission = 'admin'

    def form_valid(self, form):
        """Creates a service hook at GitHub."""
        create_hook_github(self.request, self.object)
        self.object.active = True
        # Initiates first build
        self.build = update_docs(self.object)
        logger.info('Created hook for %s/%s' % (
            self.kwargs['username'], self.kwargs['project']))
        return super(ProjectActivate, self).form_valid(form)

    def get_success_url(self):
        """Returns the url of the newly created build."""
        return reverse('project_build_detail', args=[
            self.kwargs['username'], self.kwargs['project'], self.build.pk])


class ProjectDetail(PermissionRequiredMixin, ProjectMixin, DetailView):
    """View for showing the project details."""
    required_permission = 'read'


class ProjectUpdate(PermissionRequiredMixin, ProjectMixin, UpdateView):
    """View for updating project details."""
    form_class = ProjectActivateForm
    required_permission = 'admin'

    def form_valid(self, form):
        """Logs updating of the project."""
        logger.info('Updated project %s' % self.kwargs['project'])
        return super(ProjectUpdate, self).form_valid(form)


class ProjectDelete(PermissionRequiredMixin, ProjectMixin, DeleteView):
    """View for delting a project."""
    required_permission = 'admin'

    def get_success_url(self):
        """Returns the URL of the user's detail_view."""
        logger.info('Deleted project %s' % self.kwargs['project'])
        return self.request.user.get_absolute_url()


class ProjectBuildList(ListView):
    """View for showing the list of builds for a project."""
    # TODO: permission check needs to be done for listing builds

    def get_queryset(self):
        """Returns the builds for the project."""
        return Build.objects.filter(
            project__owner__login=self.kwargs['username'],
            project__name=self.kwargs['project']
        )

    def get_context_data(self, **kwargs):
        """Sets the list of Heroku apps as context."""
        context = super(ProjectBuildList, self).get_context_data(**kwargs)
        context['owner'] = self.kwargs['username']
        context['project'] = self.kwargs['project']
        return context


class ProjectBuildDetail(PermissionRequiredMixin, DetailView):
    """View for showing the build detail for a project."""
    model = Build
    required_permission = 'read'


class ProjectDocs(View):
    """View for showing the project's built documentation."""

    def get(self, request, *args, **kwargs):
        """Returns the index.html file."""
        return serve(request, self.kwargs['project'], 'index.html')


def import_from_heroku(request):
    """Imports a project from a Heroku app."""
    if request.method == 'POST':
        logger.info('Importing an app from Heroku')
        api_key = request.user.get_profile().heroku_api_key
        r = requests.get('%s/apps/%s' % (
            settings.HEROKU_API_URL, request.POST['app_name']
        ), auth=('', api_key))
        app = r.json()
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
        update_docs(project)
        return HttpResponseRedirect(
            reverse('project_detail', args=[request.user, project]))
    else:
        raise Http404


def create_hook_github(request, project):
    """Creates a post-receive hook for the given project at the GitHub repo."""
    logger.info('Creating a post-receive hook at GitHub')
    access_token = request.user.github_access_token
    url = request.build_absolute_uri(reverse('github_hook'))
    config = {'url': url}
    payload = {'name': 'web', 'config': config}
    r = requests.post('%s/repos/%s/%s/hooks' % (
        settings.GITHUB_API_URL, project.owner.login, project.name
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
