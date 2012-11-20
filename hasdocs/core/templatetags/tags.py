from django import template
from django.core.urlresolvers import reverse_lazy

register = template.Library()


@register.simple_tag
def active(path, url):
    if path == reverse_lazy(url):
        return 'active'
    else:
        return ''