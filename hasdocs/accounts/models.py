from django.contrib.auth.models import User
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

class UserType(models.Model):
    """Type of a user (e.g. individual user or organization)."""
    # Name of the user type
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
class UserProfile(models.Model):
    """Model for representing user profiles."""
    # One-to-one mapping to the auth user model
    user = models.OneToOneField(User)
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