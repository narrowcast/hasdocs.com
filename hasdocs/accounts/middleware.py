from hasdocs.accounts.backends import GithubBackend
from hasdocs.accounts.models import AnonymousUser

SESSION_KEY = '_auth_user_id'


class AuthenticationMiddleware(object):
    def process_request(self, request):
        try:
            user_id = request.session[SESSION_KEY]
            backend = GithubBackend()
            request.user = backend.get_user(user_id) or AnonymousUser()
        except KeyError:
            request.user = AnonymousUser()
