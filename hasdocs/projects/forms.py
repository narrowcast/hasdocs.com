from django.forms import ModelForm
from django.forms.widgets import HiddenInput

from hasdocs.projects.models import Project


class ProjectCreateForm(ModelForm):
    """Form for importing a project from GitHub."""
    class Meta:
        model = Project
        fields = ('language', 'generator', 'docs_path', 'requirements_path',
                  'owner', 'name')
        widgets = {
            'owner': HiddenInput(),
            'name': HiddenInput()
        }
