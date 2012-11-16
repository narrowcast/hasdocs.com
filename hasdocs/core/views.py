import json
import logging

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView

from hasdocs.accounts.views import UserDetailView
from hasdocs.projects.models import Project
from hasdocs.core.forms import ContactForm
from hasdocs.core.tasks import update_docs

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
        project = get_object_or_404(Project, url=repo_url)
        result = update_docs.delay(project)
        return HttpResponse('Thanks')
    else:
        return HttpResponseNotFound()
    
@csrf_exempt
def post_receive_heroku(request):
    """Post-receive hook to be hit by Heroku."""
    if request.method == 'POST':
        app_url = request.POST['url']
        logger.info('Heroku deploy hook triggered for %s' % repo_url)
        project = get_object_or_404(Project, url=app_url)
        result = update_docs.delay(project)
        return HttpResponse('Thanks')
    else:
        return HttpResponseNotFound()
    
class ContactView(FormView):
    """Shows the contact form and sends email to admin on a valid submission."""
    form_class = ContactForm
    template_name = 'core/contact.html'
    success_url = '/thanks/'
    
    def form_valid(self, form):
        """Sends emails to the admins on form validation."""
        #form.send_email()
        return super(ContactView, self).form_valid(form)