import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

logger = logging.getLogger(__name__)


class Generator(models.Model):
    """Model for representing a documentation generator."""
    # Name of the documentation generator
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
class Language(models.Model):
    """Model for representing a programming language."""
    # Name of the programming language
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Project(models.Model):
    """Model for representing a software project."""
    # Owner of the project
    owner = models.ForeignKey(User)
    # Name of the project
    name = models.CharField(max_length=50)
    # Collaborators
    collaborators = models.ManyToManyField(
        User, blank=True, null=True, related_name="collaborating_project_set"
    )
    # Description of the project
    description = models.TextField(blank=True)
    # Whether this project is private or not
    private = models.BooleanField(default=False)
    # URL of the git repository
    git_url = models.CharField(max_length=200, blank=True)
    # Programming language this project is in    
    language = models.ForeignKey(Language, blank=True, null=True)
    # Documentation generator to be used for this project
    generator = models.ForeignKey(Generator, blank=True, null=True)
    # Published date
    pub_date = models.DateTimeField(auto_now_add=True)
    # Last modified date
    mod_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('project_detail', [self.owner, self.name])