from django.contrib import admin

from hasdocs.accounts.models import Plan, UserProfile, UserType


class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'private_docs', 'business')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'plan', 'company', 'location')

admin.site.register(Plan, PlanAdmin)
admin.site.register(UserType)
admin.site.register(UserProfile, UserProfileAdmin)
