from django.conf import settings
from django.contrib.auth.models import User as ContribUser
from django.db import models

from hasdocs.projects.models import Project


class Plan(models.Model):
    """Model for a plan."""
    # Name of the plan
    name = models.CharField(max_length=50)
    # Number of private docs
    private_docs = models.PositiveIntegerField()
    # Monthly price of the plan
    price = models.DecimalField(max_digits=64, decimal_places=2, default=0)
    # Whether this is a plan for an organization rather than uesr
    business = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class UserType(models.Model):
    """Type of a user (e.g. individual user or organization)."""
    # Name of the user type
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class BaseUser(models.Model):
    # Login name of the user
    login = models.CharField(max_length=100)
    # Full name of the user
    name = models.CharField(max_length=100, blank=True)
    # Email of the user
    email = models.EmailField(blank=True)
    # Gravatar ID
    gravatar_id = models.CharField(max_length=32, blank=True)
    # Blog or webiste URL
    url = models.URLField(blank=True)
    # Company
    company = models.CharField(max_length=50, blank=True)
    # Location
    location = models.CharField(max_length=50, blank=True)
    # Plan for the user
    plan = models.ForeignKey(Plan, blank=True, null=True)


class Organization(BaseUser):
    """Model for representing an organization."""
    def __unicode__(self):
        return self.login


class User(BaseUser):
    """Model for representing a user."""
    # GitHub access token
    github_access_token = models.CharField(max_length=255, blank=True)
    # Heroku API key
    heroku_api_key = models.CharField(max_length=255, blank=True)
    # Organizations this user belongs to
    organizations = models.ManyToManyField(Organization, blank=True, null=True)

    def __unicode__(self):
        return self.login


class UserProfile(models.Model):
    """Model for representing user profiles."""
    # One-to-one mapping to the auth user model
    user = models.OneToOneField(ContribUser)
    # Gravatar ID
    gravatar_id = models.CharField(max_length=32, blank=True)
    # Blog or webiste URL
    url = models.URLField(blank=True)
    # Company
    company = models.CharField(max_length=50, blank=True)
    # Location
    location = models.CharField(max_length=50, blank=True)
    # User ype (e.g., user or organization)
    user_type = models.ForeignKey(UserType, blank=True, null=True)
    # Current plan for this user
    plan = models.ForeignKey(Plan, blank=True, null=True)
    # Organizations this user belongs to
    organizations = models.ManyToManyField(User, blank=True, null=True,
                                           related_name="organization_set")
    # GitHub access token
    github_access_token = models.CharField(max_length=255, blank=True)
    # Heroku API key
    heroku_api_key = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.user.username

    def gravatar_url(self, size=210):
        """Returns the gravatar url for this user."""
        if self.gravatar_id:
            return '%s/%s?s=%s' % (settings.GRAVATAR_API_URL,
                                   self.gravatar_id, size)
        else:
            return None

    def is_organization(self):
        """Returns whether this user profile is for an organization or not."""
        return self.user_type.name == 'Organization'


class Team(models.Model):
    """Model for a team within an organization."""
    ADMIN = 'admin'
    PUSH = 'push'
    PULL = 'pull'
    PERMISSION_CHOICES = (
        (ADMIN, 'Admin'),
        (PUSH, 'Push'),
        (PULL, 'Pull'),
    )
    # Name of the team
    name = models.CharField(max_length=50)
    # The organization this team belongs to
    organization = models.ForeignKey(Organization)
    # Permission for this team (admin, push, pull)
    permission = models.CharField(max_length=5, choices=PERMISSION_CHOICES)
    # Members of the team
    members = models.ManyToManyField(User, blank=True, null=True)
    # Repositories of the team
    repos = models.ManyToManyField(Project, blank=True, null=True)

    def __unicode__(self):
        return '%s: %s' % (self.organization, self.name)
