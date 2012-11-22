import logging
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic.list import ListView

from hasdocs.projects.models import Project

logger = logging.getLogger(__name__)


class ProjectListView(ListView):
    """View for viewing the list of projects."""
    def get_queryset(self):
        """Limits the list to public projects."""
        return Project.objects.filter(private=False)

class ProjectDetailView(DetailView):
    """View for showing the project details."""
    model = Project
    slug_field = 'name'
    context_object_name = 'project'
    
    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name=kwargs['slug'])
        if project.private and request.user != project.owner:
            # Then just raise 404
            raise Http404
        return super(ProjectDetailView, self).dispatch(request, *args, **kwargs)

class ProjectUpdateView(UpdateView):
    """View for updating project details."""
    model = Project
    slug_field = 'name'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name=kwargs['slug'])
        if request.user != project.owner:
            raise Http404
        return super(ProjectUpdateView, self).dispatch(request, *args, **kwargs)

class ProjectDeleteView(DeleteView):
    """View for delting a project."""
    model = Project
    slug_field = 'name'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name=kwargs['slug'])
        if request.user != project.owner:
            raise Http404
        return super(ProjectDeleteView, self).dispatch(request, *args, **kwargs)

class GitHubProjectListView(TemplateView):
    """View for viewing the list of GitHub projects."""
    template_name = 'projects/project_list_github.html'
    
    def get_context_data(self, **kwargs):
        """Sets the list of GitHub repositories as context."""
        context = super(GitHubProjectListView, self).get_context_data(**kwargs)        
        access_token = self.request.user.get_profile().github_access_token
        payload = {'access_token': access_token }
        r = requests.get('%s/user/repos' % settings.GITHUB_API_URL,
                         params=payload)
        context['repos'] = r.json
        return context

class HerokuProjectListView(TemplateView):
    """View for viewing the list of Heroku projects."""
    template_name = 'projects/project_list_heroku.html'
    
    def get_context_data(self, **kwargs):
        """Sets the list of Heroku apps as context."""
        context = super(HerokuProjectListView, self).get_context_data(**kwargs)
        api_key = self.request.user.get_profile().heroku_api_key
        r = requests.get('%s/apps' % settings.HEROKU_API_URL,
                         auth=('', api_key))
        context['apps'] = r.json
        return context
    
def import_from_github(request):
    """Imports a project from GitHub repository."""
    access_token = request.user.get_profile().github_access_token
    payload = {'access_token': access_token }
    r = requests.get('%s/repos/%s' % (
        settings.GITHUB_API_URL, request.POST['full_name']), params=payload)
    repo = r.json
    # Creates a new project based on the GitHub repo
    project = Project(name=repo['name'], description=repo['description'],
                      private=repo['private'])
    project.save()
    
def import_from_heroku(request):
    """Imports a project from Heroku app."""
    api_key = request.user.get_profile().heroku_api_key
    r = requests.get('%s/apps/%s' % (
        settings.HEROKU_API_URL, request.POST['app_name']), auth=('', api_key))
    app = r.json
    # Creates a new project based on the Heroku app
    project = Project(name=app['name'], url=app['web_url'],
                      git_url=app['git_url'], private=True)
    project.save()