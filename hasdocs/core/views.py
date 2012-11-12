from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    """Shows the home page."""
    return render_to_response('core/index.html', {
    }, context_instance=RequestContext(request))