from django.contrib import admin

from hasdocs.accounts.models import Plan, UserProfile, UserType
from hasdocs.accounts.models import User, Organization


class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'private_docs', 'business')


class UserAdmin(admin.ModelAdmin):
    list_display = ('login', 'name', 'email', 'company', 'location', 'plan')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'plan', 'company', 'location')

admin.site.register(Organization, UserAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserType)
admin.site.register(UserProfile, UserProfileAdmin)
