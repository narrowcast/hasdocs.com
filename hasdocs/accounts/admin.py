from django.contrib import admin

from hasdocs.accounts.models import UserProfile, UserType

admin.site.register(UserType)
admin.site.register(UserProfile)