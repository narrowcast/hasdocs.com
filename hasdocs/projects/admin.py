from django.contrib import admin

from hasdocs.projects.models import Domain, Generator, Language, Project


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'language', 'generator', 'url', 'description')

admin.site.register(Domain)
admin.site.register(Generator)
admin.site.register(Language)
admin.site.register(Project, ProjectAdmin)