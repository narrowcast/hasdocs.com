import logging

from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models

from hasdocs.accounts.models import BaseUser, OthersPermission, Team, User

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


class ProjectManager(models.Manager):
    """Manager for returning various project sets."""

    def owned_by(self, account, user):
        """Returns the projects owned by given user or organization account."""
        queryset = Project.objects.filter(owner=account)
        if not user.is_authenticated():
            # Then only return public projects
            return queryset.filter(private=False)
        if account.is_organization():
            if user.is_owner(account):
                # Then return everything
                return queryset
            elif account.members.filter(pk=user.pk).exists():
                # Then return only the repos that user's teams have access to
                public_set = queryset.filter(private=False)
                member_set = queryset.filter(teams=user.team_set.all)
                return (public_set | member_set).distinct()
            else:
                return queryset.filter(private=False)
        else:
            if user.is_owner(account):
                # Then return everything
                return queryset
            else:
                # Then return only the repos that user is collaborating on
                public_set = queryset.filter(private=False)
                member_set = queryset.filter(collaborators=user)
                return (public_set | member_set).distinct()


class Project(models.Model):
    """Model for representing a software project."""
    # Owner of the project
    owner = models.ForeignKey(BaseUser)
    # Name of the project
    name = models.CharField(max_length=100)
    # Collaborators for the project
    collaborators = models.ManyToManyField(
        User, blank=True, null=True, related_name='collaborating_project_set')
    # Collaborating teams for the project
    teams = models.ManyToManyField(Team, blank=True, null=True)
    # Description of the project
    description = models.TextField(blank=True)
    # Whether this project is actively being built
    active = models.BooleanField()
    # Whether this project is private or not
    private = models.BooleanField(default=False)
    # Project's GitHub repo or Heroku app URL
    html_url = models.CharField(max_length=200, blank=True, unique=True)
    # URL of the git repository
    git_url = models.CharField(max_length=200, blank=True)
    # Programming language this project is in
    language = models.ForeignKey(
        Language, blank=True, null=True,
        help_text="Choose the programming language this repository uses."
    )
    # Documentation generator to be used for this project
    generator = models.ForeignKey(
        Generator, blank=True, null=True,
        help_text="Choose the documentation generator for this repository."
    )
    # Path to the requirements file
    requirements_path = models.CharField(
        max_length=200, blank=True,
        help_text="Specify the path of the pip requirements file, if any."
    )
    # Path to the directory containing Sphinx documentation
    docs_path = models.CharField(
        max_length=200, default='docs',
        help_text="Specify the path of documenations relative to project root."
    )
    # Published date
    pub_date = models.DateTimeField(auto_now_add=True)
    # Last modified date
    mod_date = models.DateTimeField(auto_now=True)
    # Custom manager for the model
    objects = ProjectManager()

    class Meta:
        permissions = (
            ('admin', 'Administer project'),
            ('push', 'Push to the repositories'),
            ('pull', 'Make pull requests'),
        )

    def __unicode__(self):
        return self.name

    @classmethod
    def from_kwargs(cls, **kwargs):
        """Creates and returns a new project from the given kwargs."""
        owner = BaseUser.objects.get(id=kwargs.pop('owner')['id'])
        try:
            project = Project.objects.get(owner=owner, id=kwargs['id'])
        except Project.DoesNotExist:
            project = Project(owner=owner, id=kwargs['id'])
        for key, value in project.__dict__.iteritems():
            if key in kwargs:
                setattr(project, key, kwargs.get(key))
        # TODO: Quick hack to handle cases where description is None
        if not project.description:
            project.description = ''
        # Sets project language
        try:
            language = Language.objects.get(name=kwargs['language'])
            project.language = language
        except Language.DoesNotExist:
            logger.warning('Failed to find language %s' % kwargs['language'])
        project.save()
        path = '/%s/%s/' % (owner.login, project.name)
        OthersPermission.objects.filter(path=path).delete()
        if not project.private:
            OthersPermission.objects.create(path=path, permission='read')
        return project

    def is_owner(self, user):
        """Returns whether the user is owner of this project."""
        if self.owner.is_organization():
            # Then the user must be owner of the organization
            return self.owner.organization.team_set.get(
                name='Owners').members.filter(pk=user.pk).exists()
        else:
            # Then the user must be the owner
            return user == self.owner.user

    def is_member(self, user):
        """Returns whether the user is member of this project."""
        if self.owner.is_organization():
            # Then the user must be member of the team that has this project
            return (self.owner.organization.team_set.all() &
                    user.team_set.all())
        else:
            # Then the user must be in the collaborators
            return self.collaborators.filter(pk=user.pk).exists()

    def has_perm(self, user, permission):
        """Returns ture if the user has requested permission for project."""
        if permission == 'admin':
            return self.is_owner(user)
        elif permission == 'pull':
            if self.is_owner(user):
                return True
            elif self.private:
                return self.is_member(user)
            else:
                return True

    @models.permalink
    def get_absolute_url(self):
        """Returns the url for this project."""
        return ('project_detail', [self.owner, self.name])

    def get_docs_url(self):
        """Returns the url of the docs for this project."""
        site = Site.objects.get_current().domain
        return 'http://%s.%s/%s/' % (self.owner, site, self.name)

    def get_latest_build(self):
        """Returns the latest documentation build for this project."""
        try:
            return self.build_set.order_by('-number')[0:1].get()
        except Build.DoesNotExist:
            return None


class Build(models.Model):
    """Model for representing a documentation build."""
    SUCCESS = 'S'
    FAILURE = 'F'
    UNKNOWN = 'U'
    STATUS_CHOICES = (
        (SUCCESS, 'Success'),
        (FAILURE, 'Failure'),
        (UNKNOWN, 'Unknown'),
    )
    # The project this build is for
    project = models.ForeignKey(Project)
    # Build number for the project
    number = models.IntegerField()
    # Status of the build (e.g., building, finished, or failed)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    # Output from running the build
    output = models.TextField(blank=True)
    # Time it started building the documentation
    started_at = models.DateTimeField(auto_now_add=True)
    # Time it finished building the documentation
    finished_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __unicode__(self):
        return '%s/%s: %s' % (
            self.project.owner.login, self.project.name, self.number)

    def save(self, *args, **kwargs):
        """Numbers itself after the latest build for the project."""
        if not self.pk:
            last_build = self.project.get_latest_build()
            self.number = last_build.number + 1 if last_build else 1
        super(Build, self).save(*args, **kwargs)

    def duration(self):
        """Returns the time it took for this build to build."""
        return self.finished_at - self.started_at

    @models.permalink
    def get_absolute_url(self):
        """Returns the url for this project."""
        return ('project_build_detail',
                [self.project.owner.login, self.project.name, self.pk])


class Domain(models.Model):
    """Model for representing a domain name."""
    # URL of the domain
    name = models.CharField(max_length=200)
    # The project this domain is for
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.name
