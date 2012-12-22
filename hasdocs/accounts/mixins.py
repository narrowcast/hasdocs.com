import re

from django.http import Http404

from hasdocs.accounts.models import GroupPermission, OthersPermission, \
    UserPermission


class PermissionRequiredMixin(object):
    """A mixin for requiring permission to access a single object."""

    def _has_perms(self, user, perms):
        user.perms = perms.values_list('permission', flat=True)
        return perms.filter(permission=self.required_permission).exists()

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request, 'subdomain'):
            path = '/%s%s' % (request.subdomain, request.path)
        else:
            path = request.path
        # Hack to match sub-project level urls
        path = re.match('^/[\w-]+/[\w.-]+/', path).group()
        # Checks for user-level permission first
        user_perms = UserPermission.objects.filter(
            user=request.user, path=path
        )
        if self._has_perms(request.user, user_perms):
            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)
        # Then checks for group permission
        group_perms = GroupPermission.objects.filter(
            group__members=request.user, path=path
        )
        if self._has_perms(request.user, group_perms):
            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)
        # Then checks for others permission
        others_perms = OthersPermission.objects.filter(path=path)
        if self._has_perms(request.user, others_perms):
            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)
        else:
            raise Http404
