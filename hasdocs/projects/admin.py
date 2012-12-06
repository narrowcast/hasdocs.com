from django.contrib import admin

from hasdocs.projects.models import Domain, Generator, Language, Project


class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'language', 'generator', 'private',
                    'description')

admin.site.register(Domain, DomainAdmin)
admin.site.register(Generator)
admin.site.register(Language)
admin.site.register(Project, ProjectAdmin)
