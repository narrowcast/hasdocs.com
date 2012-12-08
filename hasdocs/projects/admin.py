from django.contrib import admin

from hasdocs.projects.models import Build, Domain, Generator, Language, Project


class BuildAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'status', 'duration', 'finished_at')


class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'language', 'generator', 'private',
                    'description')

admin.site.register(Build, BuildAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Generator)
admin.site.register(Language)
admin.site.register(Project, ProjectAdmin)
