from django.contrib import admin

from hasdocs.accounts.models import GroupPermission, Organization, \
    OthersPermission, Plan, Team, User, UserPermission


class GroupPermissionAdmin(admin.ModelAdmin):
    list_display = ('group', 'permission', 'path')


class OthersPermissionAdmin(admin.ModelAdmin):
    list_display = ('permission', 'path')


class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'private_docs', 'business')


class TeamAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'organization', 'permission')


class UserAdmin(admin.ModelAdmin):
    list_display = ('login', 'name', 'email', 'company', 'location', 'plan')


class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission', 'path')


admin.site.register(GroupPermission, GroupPermissionAdmin)
admin.site.register(Organization, UserAdmin)
admin.site.register(OthersPermission, OthersPermissionAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserPermission, UserPermissionAdmin)
