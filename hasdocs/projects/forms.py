from django.forms import ModelForm

from hasdocs.projects.models import Project


class ProjectActivateForm(ModelForm):
    """Form for creating a post-receive hook for a project."""
    class Meta:
        model = Project
        fields = ('language', 'generator', 'docs_path', 'requirements_path')
