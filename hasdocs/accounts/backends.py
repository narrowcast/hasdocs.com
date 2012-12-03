import logging

from django.contrib.auth.models import User

from hasdocs.accounts.models import UserProfile

logger = logging.getLogger(__name__)


class GithubBackend(object):
    """Authentication using the GitHub access token."""
    def authenticate(self, access_token):
        """Receives the user's login from GitHub and authenticates the user."""
        logger.info('Authenticating a user with GitHub access token')
        try:
            profile = UserProfile.objects.get(github_access_token=access_token)
            return profile.user
        except UserProfile.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """Returns the authenticated user."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None