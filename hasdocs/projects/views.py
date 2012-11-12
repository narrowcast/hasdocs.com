from django.views.generic import DetailView

from hasdocs.projects.models import Project


class ProjectDetailView(DeailView):
    """View for showing the project details."""
    model = Project
    context_object_name = 'project'
    template_name='projects/project_detail.html'