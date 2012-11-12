from django.contrib import admin

from hasdocs.projects.models import Generator, Language, Project


admin.site.register(Generator)
admin.site.register(Language)
admin.site.register(Project)