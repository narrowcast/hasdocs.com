import json
import logging

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from hasdocs.accounts.views import UserDetailView
from hasdocs.projects.models import Project
from hasdocs.core.tasks import build_docs

logger = logging.getLogger(__name__)


def home(request):
    """Shows the home page or user page."""
    if request.subdomain:
        # Then serve the page for the given user, if any
        user = get_object_or_404(User, username=request.subdomain)
        return HttpResponse('Found a matching user.')
    else:
        return render_to_response('core/index.html', {
        }, context_instance=RequestContext(request))
    
def user_or_page(request, slug):
    """Shows the project page if subdomain is set or the user detail."""
    if request.subdomain:
        # Then serve the project page for the given user and project, if any
        user = get_object_or_404(User, username=request.subdomain)
        project = get_object_or_404(Project, name=slug)
        return HttpResponse('Found a matching user and project combo.')
    else:
        # Then server the user detail for the given user
        user = get_object_or_404(User, username=slug)
        return render_to_response('accounts/user_detail.html', {
            'account': user
        }, context_instance=RequestContext(request))
    
@csrf_exempt
def post_receive_github(request):
    """Post-receive hook to be hit by GitHub."""
    if request.method == 'POST':
        payload = json.loads(request.POST['payload'])
        repo_url = payload['repository']['url']        
        logger.info('GitHub post-receive hook triggered for %s' % repo_url)
        #project = Project.objects.get(git_url=repo_url)
        #build_docs.delay(project)
        return HttpResponse('Thanks')
    else:
        return HttpResponseNotFound()