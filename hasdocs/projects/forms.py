from django.forms import ModelForm

from hasdocs.projects.models import Project


class ProjectActivateForm(ModelForm):
    """Form for importing a project from GitHub."""
    class Meta:
        model = Project
        fields = ('language', 'generator', 'docs_path', 'requirements_path')
