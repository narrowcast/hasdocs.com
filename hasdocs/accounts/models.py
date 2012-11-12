from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save


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
    user_type = models.ForeignKey(UserType)
    # GitHub access token
    github_access_token = models.CharField(max_length=255, blank=True)
    # Heroku API key
    heroku_api_key = models.CharField(max_length=255, blank=True)
    
    def __unicode__(self):
        return self.user.username

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)