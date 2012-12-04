from django.forms import ModelForm
 
from hasdocs.projects.models import Project
 
 
class ProjectCreateForm(ModelForm):
    """Form for importing a project from GitHub."""
    class Meta:
        model = Project
