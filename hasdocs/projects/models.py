import logging

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models

logger = logging.getLogger(__name__)


class Domain(models.Model):
    """Model for representing a domain name."""
    # URL of the domain
    name = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.name
    
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
    # Project's GitHub repo or Heroku app URL
    url = models.CharField(max_length=200, blank=True, unique=True)
    # URL of the git repository
    git_url = models.CharField(max_length=200, blank=True)
    # Programming language this project is in    
    language = models.ForeignKey(Language, blank=True, null=True)
    # Documentation generator to be used for this project
    generator = models.ForeignKey(Generator, blank=True, null=True)
    # Custom domains for this project
    custom_domains = models.ManyToManyField(Domain, blank=True, null=True)
    # Path to the requirements file
    requirements_path = models.CharField(max_length=200, blank=True)
    # Path to the directory containing Sphinx documentation
    docs_path = models.CharField(max_length=200, default='docs')
    # Published date
    pub_date = models.DateTimeField(auto_now_add=True)
    # Last modified date
    mod_date = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        """Returns the url for this project."""
        return ('project_detail', [self.owner, self.name])
    
    def get_docs_url(self):
        """Returns the url of the docs for this project."""
        site = Site.objects.get_current().domain
        return 'http://%s.%s/%s/' % (self.owner, site, self.name)
