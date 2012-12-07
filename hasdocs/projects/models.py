import logging

from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models

logger = logging.getLogger(__name__)
docs_storage = S3BotoStorage(
    bucket=settings.AWS_DOCS_BUCKET_NAME, acl='private',
    reduced_redundancy=True, secure_urls=False
)


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
    name = models.CharField(max_length=100)
    # slug of the project which is username/project
    slug = models.SlugField()
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

    def get_logs(self):
        """Returns the log for the latest build from S3."""
        path = '%s/%s/logs.txt' % (self.owner, self.name)
        try:
            with docs_storage.open(path, 'r') as file:
                return file.read()
        except IOError:
            return 'No logs were found.'

    def get_errs(self):
        """Returns the error log for the latest build from S3."""
        path = '%s/%s/errs.txt' % (self.owner, self.name)
        try:
            with docs_storage.open(path, 'r') as file:
                return file.read()
        except IOError:
            return 'No logs were found.'

    def get_latest_build(self):
        """Returns the latest documentation build for this project."""
        try:
            return self.build_set.order_by('-number')[0:1].get()
        except Build.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        """Builds the slug from owner's username and project name."""
        self.slug = '%s/%s' % (self.owner.username, self.name)
        return super(Project, self).save(*args, **kwargs)


class Build(models.Model):
    """Model for representing a documentation build."""
    STATUS_CHOICES = (
        ('S', 'Success'),
        ('F', 'Failure'),
        ('U', 'Unknown'),
    )    
    # The project this build is for
    project = models.ForeignKey(Project)
    # Build number for the project
    number = models.IntegerField()
    # Status of the build (e.g., building, finished, or failed)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    # Time it started building the documentation
    started_at = models.DateTimeField(auto_now_add=True)
    # Time it finished building the documentation
    finished_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-number']

    def __unicode__(self):
        return '%s: %s' % (self.project.name, self.number)
    
    def duration(self):
        """Returns the time it took for this build to build."""
        return self.finished_at - self.started_at
    
    @models.permalink
    def get_absolute_url(self):
        """Returns the url for this project."""
        return ('project_build_detail',
                [self.project.owner.username, self.project.name, self.pk])


class Domain(models.Model):
    """Model for representing a domain name."""
    # URL of the domain
    name = models.CharField(max_length=200)
    # The project this domain is for
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.name
