import re

from django.conf import settings
from django.db import models


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


class AnonymousUser(models.Model):
    """Model for an anonoymous user."""
    is_active = False

    def is_authenticated(self):
        return False

    def is_owner(self, account):
        return False


class BaseUser(models.Model):
    """Model for base user."""
    # Username of the user
    login = models.CharField(max_length=100, unique=True)
    # Full name of the user
    name = models.CharField(max_length=100, blank=True)
    # Email of the user
    email = models.EmailField(blank=True)
    # Whether this user is active or not
    is_active = models.BooleanField(default=True)
    # Gravatar ID
    gravatar_id = models.CharField(max_length=32, blank=True)
    # Blog or webiste URL
    blog = models.URLField(blank=True)
    # Company
    company = models.CharField(max_length=100, blank=True)
    # Location
    location = models.CharField(max_length=100, blank=True)
    # Plan for the user
    plan = models.ForeignKey(Plan, blank=True, null=True)
    # Date the user has joined
    date_joined = models.DateTimeField(auto_now_add=True)
    # Date last synchronized with GitHub
    github_sync_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.login

    @classmethod
    def from_kwargs(cls, **kwargs):
        """Returns the existing baseuser for the kwargs or creates one."""
        baseuser, created = cls.objects.get_or_create(
            id=kwargs['id'], login=kwargs['login'])
        baseuser.is_active = True
        for key, value in baseuser.__dict__.iteritems():
            if key in kwargs and kwargs.get(key):
                setattr(baseuser, key, kwargs.get(key))
        baseuser.save()
        return baseuser

    def is_authenticated(self):
        return True

    def is_organization(self):
        """Returns if this BaseUser is an Organization or not."""
        try:
            return self.organization
        except Organization.DoesNotExist:
            return False

    @models.permalink
    def get_absolute_url(self):
        """Returns the url for this user."""
        return ('user_detail', [self.login])

    def gravatar_url(self, size=210):
        """Returns the gravatar url for this user."""
        if self.gravatar_id:
            return '%s/%s?s=%s' % (settings.GRAVATAR_API_URL,
                                   self.gravatar_id, size)
        else:
            return ''


class User(BaseUser):
    """Model for representing a user."""
    # GitHub access token
    github_access_token = models.CharField(max_length=255, blank=True)
    # Heroku API key
    heroku_api_key = models.CharField(max_length=255, blank=True)

    def is_owner(self, account):
        """Returns whehter the user is the owner of the account."""
        if account.is_organization():
            try:
                return account.team_set.get(name='Owners').members.filter(
                    pk=self.pk).exists()
            except Team.DoesNotExist:
                return False
        else:
            return self == account


class Organization(BaseUser):
    """Model for representing an organization."""
    # Billing email address for this organization
    billing_email = models.EmailField()
    # Members of this organization
    members = models.ManyToManyField(User, blank=True, null=True)

    def active_members(self):
        """Returns only the active members of the organization."""
        return self.members.filter(is_active=True)

    def is_organization(self):
        return True

    @classmethod
    def from_kwargs(cls, **kwargs):
        """Returns the existing organization for the kwargs or creates one."""
        org = super(Organization, cls).from_kwargs(**kwargs)
        if 'avatar_url' in kwargs:
            match = re.match('.+/avatar/(?P<hashcode>\w+)?.+',
                             kwargs['avatar_url'])
            org.gravatar_id = match.group('hashcode')
        org.save()
        return org


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

    class Meta:
        unique_together = ('name', 'organization')

    def __unicode__(self):
        return '%s: %s' % (self.organization, self.name)

    @classmethod
    def from_kwargs(cls, organization=None, **kwargs):
        """Returns the existing team for the given kwargs or creates one."""
        team, created = cls.objects.get_or_create(
            organization=organization, id=kwargs['id'])
        for key, value in team.__dict__.iteritems():
            if key in kwargs:
                setattr(team, key, kwargs.get(key))
        team.organization = organization
        team.save()
        return team


class BasePermission(models.Model):
    """Model for representing a base object-level permission."""
    # URL for which this permission is applied
    path = models.CharField(max_length=200)
    # Permission
    permission = models.CharField(max_length=50)

    class Meta:
        abstract = True

    def __unicode__(self):
        account = getattr(self, 'user', False) or self.group
        return '%s can %s %s' % (account, self.permission, self.path)


class UserPermission(BasePermission):
    """Model for an object-level permission for a user."""
    # User who is associated with this permission
    user = models.ForeignKey(User)

    class Meta:
        unique_together = ('user', 'path', 'permission')


class GroupPermission(BasePermission):
    """Model for an object-level permission for a group."""
    # Group that is associated with this permission
    group = models.ForeignKey(Team)

    class Meta:
        unique_together = ('group', 'path', 'permission')


class OthersPermission(BasePermission):
    """Model for an object-level permission for others."""

    class Meta:
        unique_together = ('path', 'permission')

    def __unicode__(self):
        return 'everyone can %s %s' % (self.permission, self.path)
