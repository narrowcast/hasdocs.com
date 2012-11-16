from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.simple_tag
def active(request, urls):
    if request.path in (reverse(url) in urls.split()):
        return 'active'
    return ''