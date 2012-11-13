from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from hasdocs.accounts.views import UserDetailView
from hasdocs.projects.models import Project


def home(request):
    """Shows the home page or user page."""
    if request.subdomain:
        # Then serve the page for the given user, if any
        user = get_object_or_404(User, username=request.subdomain)
        return HttpResponse("Found a matching user.")
    else:
        return render_to_response('core/index.html', {
        }, context_instance=RequestContext(request))
    
def user_or_page(request, slug):
    """Shows the project page if subdomain is set or the user detail."""
    if request.subdomain:
        # Then serve the project page for the given user and project, if any
        user = get_object_or_404(User, username=request.subdomain)
        project = get_object_or_404(Project, name=slug)
        return HttpResponse("Found a matching user and project combo.")
    else:
        # Then server the user detail for the given user
        user = get_object_or_404(User, username=slug)
        return render_to_response('accounts/user_detail.html', {
            'account': user
        }, context_instance=RequestContext(request))