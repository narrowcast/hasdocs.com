from functools import wraps

from django.http import Http404

from hasdocs.accounts.models import GroupPermission, OthersPermission, \
    UserPermission


def permission_required(permission):
    """Decorator for views that require permission."""
    def decorator(function):
        @wraps(function)
        def wrapped_view(request, project, path):
            perm_path = '/%s/%s/' % (request.subdomain, project)
            # Checks for user permissions
            if UserPermission.objects.filter(
                user=request.user, path=perm_path, permission=permission
            ).exists():
                return function(request, project, path)
            # Checks for group permissions
            elif GroupPermission.objects.filter(
                group__members=request.user, path=perm_path,
                permission=permission
            ).exists():
                return function(request, project, path)
            # Checks for others permissions
            elif OthersPermission.objects.filter(
                path=perm_path, permission=permission
            ).exists():
                return function(request, project, path)
            else:
                raise Http404
        return wrapped_view
    return decorator
