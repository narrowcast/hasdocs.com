import json
import logging
import mimetypes
import os

from storages.backends.gs import GSBotoStorage

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from hasdocs.accounts.models import Plan
from hasdocs.core.forms import ContactForm
from hasdocs.core.tasks import update_docs
from hasdocs.projects.models import Domain, Project

logger = logging.getLogger(__name__)
gs_storage = GSBotoStorage(access_key=settings.GS_ACCESS_KEY_ID,
                           secret_key=settings.GS_SECRET_ACCESS_KEY)

def home(request):
    """Shows the home page."""
    return render_to_response('core/index.html', {
        }, context_instance=RequestContext(request))

def has_permission(user, project):
    """Returns whether the user has permission to access the project."""
    if project.private:
        if not user.is_authenticated():
            return False
        else:
            return user == project.owner or project.collaborators.filter(
                pk=user.pk).exists()
    else:
        # Then everyone has access to the project
        return True

def user_detail(request, slug):
    """Shows the user detail page."""
    # Then server the user detail for the given user
    user = get_object_or_404(User, username=slug)
    projects = Project.objects.filter(owner=user)
    if user != request.user:
        # Then limit access to the public projects
        projects = projects.filter(private=False)
    return render_to_response('accounts/user_detail.html', {
        'account': user, 'projects': projects,
    }, context_instance=RequestContext(request))

def get_cached_file_or_fetch(path):
    """Returns cached content for the given path or fetches and caches it."""
    if cache.has_key(path):
        return cache.get(path)
    else:
        #file = gs_storage.open(path, 'r')
        file = default_storage.open(path, 'r')
        content = file.read()
        cache.set(path, content)
        return content

def user_page(request):
    """Returns the page for the user, if any."""
    user = get_object_or_404(User, username=request.subdomain)
    path = '%s%s/index.html' % (settings.DOCS_URL, user)
    try:
        content = get_cached_file_or_fetch(path)
    except IOError:
        raise Http404
    logger.info('Serving user page at %s' % path)
    return HttpResponse(content, content_type='text/html')

def project_page(request, slug):
    """Returns the project page for the given user and project, if any."""
    user = get_object_or_404(User, username=request.subdomain)
    project = get_object_or_404(Project, name=slug)
    # Check permissions
    if not has_permission(request.user, project):
        raise Http404
    path = '%s%s/%s/index.html' % (settings.DOCS_URL, user, project)
    try:
        content = get_cached_file_or_fetch(path)
    except IOError:
        raise Http404
    logger.info('Serving project page at %s' % path)
    return HttpResponse(content, content_type='text/html')

def custom_domain_page(request):
    """Returns the project page for cnamed requests."""
    host = request.get_host()
    domain = get_object_or_404(Domain, name=host)
    project = get_object_or_404(Project, custom_domains=domain)
    # Check permissions
    if not has_permission(request.user, project):
        raise Http404
    path = '%s%s/%s/index.html' % (settings.DOCS_URL, project.owner, project)
    try:
        content = get_cached_file_or_fetch(path)
    except IOError:
        raise Http404
    logger.info('Serving custom domain page at %s from %s' % (path, host))
    return HttpResponse(content, content_type='text/html')

@cache_control(must_revalidate, max_age=3600)
def serve_static(request, slug, path):
    """Returns the requested static file from S3, inefficiently."""
    # Then serve the page for the given user, if any
    user = get_object_or_404(User, username=request.subdomain)
    try:
        path = 'docs/%s/%s/%s' % (user, slug, path)
        logger.debug('Serving static file at %s' % path)
        content = get_cached_file_or_fetch(path)
    except IOError:
        raise Http404
    return HttpResponse(content, content_type=mimetypes.guess_type(path)[0])

@cache_control(must_revalidate=True, max_age=3600)
def serve_static_cname(request, path):
    """Returns the requested static file using cname from S3, inefficiently."""
    host = request.get_host()
    domain = get_object_or_404(Domain, name=host)
    project = get_object_or_404(Project, custom_domains=domain)
    try:
        path = '%s%s/%s/%s' % (settings.DOCS_URL, project.owner, project, path)
        logger.debug('Serving static file at %s' % path)
        content = get_cached_file_or_fetch(path)
    except IOError:
        raise Http404
    return HttpResponse(content, content_type=mimetypes.guess_type(path)[0])

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
        raise Http404
    
@csrf_exempt
def post_receive_heroku(request):
    """Post-receive hook to be hit by Heroku."""
    if request.method == 'POST':
        app_url = request.POST['url']
        logger.info('Heroku deploy hook triggered for %s' % app_url)
        project = get_object_or_404(Project, url=app_url)
        result = update_docs.delay(project)
        return HttpResponse('Thanks')
    else:
        raise Http404

class PlansView(TemplateView):
    """View for showting the plans and pricing."""
    template_name="content/pricing.html"
    
    def get_context_data(self, **kwargs):
        """Sets the individual and business plans as context for the view."""
        context = super(PlansView, self).get_context_data(**kwargs)
        context['individual_plans'] = Plan.objects.filter(business=False).exclude(price=0)
        context['business_plans'] = Plan.objects.filter(business=True)
        return context
    
class ContactView(FormView):
    """Shows the contact form and sends email to admin on a valid submission."""
    form_class = ContactForm
    template_name = 'core/contact.html'
    success_url = '/thanks/'
    
    def form_valid(self, form):
        """Sends emails to the admins on form validation."""
        logger.info('Emailing admins of new contact form')
        #form.send_email()
        return super(ContactView, self).form_valid(form)