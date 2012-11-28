import json
import logging
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import DeleteView, FormView, UpdateView
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
    
    def form_valid(self, form):
        """Logs updating of the project."""
        logger.info('Updated project %s' % self.kwargs['slug'])
        return super(ProjectUpdateView, self).form_valid(form)

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
    
    def get_success_url(self):
        """Returns the URL of the user's detail_view."""
        logger.info('Deleted project %s' % self.kwargs['slug'])
        return self.request.user.get_absolute_url()

class GitHubProjectListView(TemplateView):
    """View for viewing the list of GitHub projects."""
    template_name = 'projects/project_list_github.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Checks whether user has GitHub access token and redirects if not."""
        access_token = request.user.get_profile().github_access_token
        if not access_token:
            # Then redirect to GitHub OAuth view
            return HttpResponseRedirect(reverse('oauth_authenticate'))
        return super(GitHubProjectListView, self).dispatch(request, args,**kwargs)
    
    def get_context_data(self, **kwargs):
        """Sets the list of GitHub repositories as context."""
        context = super(GitHubProjectListView, self).get_context_data(**kwargs)        
        access_token = self.request.user.get_profile().github_access_token
        payload = {'access_token': access_token }
        r = requests.get('%s/user/repos' % settings.GITHUB_API_URL,
                         params=payload)
        repos = r.json
        # Mark already imported repos
        for repo in repos:
            repo['exists'] = Project.objects.filter(url=repo['html_url']).exists()
        context['repos'] = repos
        return context

class HerokuProjectListView(TemplateView):
    """View for viewing the list of Heroku projects."""
    template_name = 'projects/project_list_heroku.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Checks whether user has Heroku api key and redirects if not."""
        api_key = request.user.get_profile().heroku_api_key
        if not api_key:
            # Then redirect to Heroku OAuth view
            pass
        return super(HerokuProjectListView, self).dispatch(request, args,**kwargs)

    def get_context_data(self, **kwargs):
        """Sets the list of Heroku apps as context."""
        context = super(HerokuProjectListView, self).get_context_data(**kwargs)
        api_key = self.request.user.get_profile().heroku_api_key
        r = requests.get('%s/apps' % settings.HEROKU_API_URL,
                         auth=('', api_key))
        apps = r.json
        # Mark already imported apps
        for app in apps:
            app['exists'] = Project.objects.filter(url=app['web_url']).exists()
        context['apps'] = apps
        return context
    
def import_from_github(request):
    """Imports a project from a GitHub repository."""
    if request.method == 'POST':
        logger.info('Importing a repository from GitHub')
        access_token = request.user.get_profile().github_access_token
        payload = {'access_token': access_token }
        r = requests.get('%s/repos/%s/%s' % (
            settings.GITHUB_API_URL,request.POST['owner'], request.POST['repo']
        ), params=payload)
        repo = r.json
        # Creates a new project based on the GitHub repo
        project = Project(owner=request.user, name=repo['name'],
                          description=repo['description'], url=repo['html_url'],
                          git_url=repo['git_url'], private=repo['private'])
        project.save()
        logger.info('Imported %s repo from GitHub.' % project.name)
        # Creates a post-receive webhook at GitHub
        create_hook_github(request)
        return HttpResponseRedirect(
            reverse('project_detail', args=[request.user, project]))
    else:
        raise Http404
    
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
        project = Project(owner=request.user, name=app['name'],
                          url=app['web_url'], git_url=app['git_url'],
                          private=True)
        project.save()
        logger.info('Imported %s app from Heroku.' % project.name)
        # Creates a post-receive webhook at GitHub
        create_hook_heroku(request)
        return HttpResponseRedirect(
            reverse('project_detail', args=[request.user, project]))
    else:
        raise Http404
    
def create_hook_github(request):
    """Creates a post-receive hook for the given project at the GitHub repo."""
    logger.info('Creating a post-receive hook at GitHub')
    access_token = request.user.get_profile().github_access_token
    url = request.build_absolute_uri(reverse('github_hook'))
    config = {'url': url, 'content_type': 'json'}
    payload = {'name': 'web', 'config': config}
    r = requests.post('%s/repos/%s/%s/hooks' % (
        settings.GITHUB_API_URL, request.POST['owner'], request.POST['repo']
    ), data=json.dumps(payload), params={'access_token': access_token})
    logger.info('Received %s from GitHub for %s' % (r, request.POST['repo']))
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
    logger.info('Received %s from Heroku for %s' % (r, request.POST['app_name']))
    return r