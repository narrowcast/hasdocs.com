import logging
import requests

from django.conf import settings
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from hasdocs.projects.models import Project

logger = logging.getLogger(__name__)


class ProjectUpdateView(UpdateView):
    """View for updating project details."""
    model = Project
    slug_field = 'name'

class ProjectDetailView(DetailView):
    """View for showing the project details."""
    model = Project
    slug_field = 'name'
    context_object_name = 'project'
    template_name='projects/project_detail.html'
    
def import_from_github(request):
    """Imports a project from GitHub repository."""
    access_token = request.user.get_profile().github_access_token
    payload = {'access_token': access_token }
    r = requests.get('%s/repos/%s' % (settings.GITHUB_API_URL,
                                      request.POST['full_name']), params=payload)
    repo = r.json
    # Creates a new project based on the GitHub repo
    project = Project(name=repo['name'], description=repo['description'],
                      private=repo['private'])
    project.save()