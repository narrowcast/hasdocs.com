import json
import logging
import mimetypes
import requests

from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import mail_managers
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, TemplateDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from hasdocs.accounts.models import Plan
from hasdocs.core.forms import ContactForm
from hasdocs.core.tasks import update_docs
from hasdocs.projects.models import Domain, Project

logger = logging.getLogger(__name__)
docs_storage = S3BotoStorage(
    bucket=settings.AWS_DOCS_BUCKET_NAME, acl='private',
    reduced_redundancy=True, secure_urls=False
)


def home(request):
    """Shows the home page."""
    return render_to_response(
        'core/index.html', context_instance=RequestContext(request))


def last_modified(request, path):
    """Returns the last modified time of the given static file."""
    username, project = path.split('/', 2)[:2]
    owner = User.objects.get(username=username)
    project = Project.objects.filter(owner=owner).get(name=project)
    return project.mod_date


@condition(last_modified_func=last_modified)
def serve(request, path):
    """Returns the requested static file from cache or S3."""
    logger.debug('Serving static file at %s' % path)
    try:
        content = cache.get(path, docs_storage.open(path, 'r').read())
        cache.add(path, content)
    except IOError:
        raise Http404
    content_type, encoding = mimetypes.guess_type(path)
    response = HttpResponse(content, content_type=content_type)
    if encoding:
        response['Content-Encoding'] = encoding
    return response


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


def user_page(request):
    """Returns the page for the user, if any."""
    user = get_object_or_404(User, username=request.subdomain)
    path = '%s/index.html' % user
    logger.info('Serving user page at %s' % path)
    return serve(request, path)


def project_page(request, slug):
    """Returns the project page for the given user and project, if any."""
    user = get_object_or_404(User, username=request.subdomain)
    project = get_object_or_404(Project, name=slug)
    # Check permissions
    if not has_permission(request.user, project):
        raise Http404
    path = '%s/%s/index.html' % (user, project)
    return serve(request, path)


def custom_domain_page(request):
    """Returns the project page for cnamed requests."""
    host = request.get_host()
    domain = get_object_or_404(Domain, name=host)
    project = domain.project
    # Check permissions
    if not has_permission(request.user, project):
        raise Http404
    path = '%s/%s/index.html' % (project.owner, project.name)
    logger.info('Serving custom domain page at %s from %s' % (path, host))
    return serve(request, path)


def serve_static(request, slug, path):
    """Returns the requested static file from S3."""
    # Then serve the page for the given user, if any
    user = get_object_or_404(User, username=request.subdomain)
    path = '%s/%s/%s' % (user, slug, path)
    return serve(request, path)


def serve_static_cname(request, path):
    """Returns the requested static file using cname from S3."""
    host = request.get_host()
    domain = get_object_or_404(Domain, name=host)
    project = domain.project
    path = '%s/%s/%s' % (project.owner, project.name, path)
    return serve(request, path)


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


def add_heroku_custom_domain(domain_name):
    """Adds a custom domain to the hasdocs Heroku app."""
    logger.info('Adding %s to hasdocs' % domain_name)
    payload = {'domain_name[domain]': domain_name}
    r = requests.post('%s/apps/hasdocs/domains' % (settings.HEROKU_API_URL),
                      auth=('', settings.HEROKU_API_KEY), data=payload)
    if r.ok:
        logger.info('%s was added to Heroku hasdocs app' % domain_name)
    else:
        logger.warnning('Failed to add %s: %s' % (domain_name, r.content))
    return r.ok


def article_detail(request, title):
    """Returns the article for the given url or 404."""
    filename = 'articles/%s.html' % title
    try:
        return render_to_response(
            filename, context_instance=RequestContext(request))
    except TemplateDoesNotExist:
        raise Http404


class Plans(TemplateView):
    """View for showting the plans and pricing."""
    template_name = "content/pricing.html"

    def get_context_data(self, **kwargs):
        """Sets the individual and business plans as context for the view."""
        context = super(Plans, self).get_context_data(**kwargs)
        context['individual_plans'] = Plan.objects.filter(
            business=False).exclude(price=0)
        context['business_plans'] = Plan.objects.filter(business=True)
        return context


class Contact(FormView):
    """Shows the contact form and sends email to admin on form submission."""
    form_class = ContactForm
    template_name = 'core/contact.html'
    success_url = '/thanks/'

    def form_valid(self, form):
        """Sends emails to the admins on form validation."""
        logger.info('Emailing admins of new contact form')
        message = '\n'.join([form.cleaned_data['name'],
                             form.cleaned_data['email'],
                             form.cleaned_data['body']])
        mail_managers(form.cleaned_data['subject'], message)
        return super(Contact, self).form_valid(form)
