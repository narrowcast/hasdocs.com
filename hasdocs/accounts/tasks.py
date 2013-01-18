import datetime

import celery
import requests

from django.conf import settings
from django.utils.timezone import utc

from hasdocs.accounts.models import GroupPermission, Team, User, UserPermission
from hasdocs.projects.models import Project

logger = celery.utils.log.get_task_logger(__name__)


def github_api_get(url, params=None):
    """Returns the requested data using GitHub's API."""
    r = requests.get('%s%s?per_page=100' % (settings.GITHUB_API_URL, url),
                     params=params)
    if not r.ok:
        logger.warning('From GitHub: %s %s' % (r.status_code, r.reason))
        raise IOError(r.status_code, r.reason)
    data = r.json()
    while r.links.get('next'):
        # Then there is more data to fetch
        r = requests.get(r.links['next']['url'])
        data += r.json()
    return data


@celery.task
def sync_user_repos_github(user, payload):
    """Sync the repositories of a user with GitHub."""
    logger.info('Syncing repositories for %s with GitHub' % user)
    repos = github_api_get('/user/repos?type=owner', params=payload)
    for repo in repos:
        project = Project.from_kwargs(**repo)
        logger.info('Project %s has been synced' % project.name)
    logger.info('Repositories have been synced for %s' % user)


@celery.task
def sync_user_collaborators_github(user, payload):
    """Syncs the collaborators for a user's repos with GitHub."""
    logger.info('Syncing collaborators for %s with GitHub' % user)
    for project in user.project_set.all():
        collaborators = github_api_get('/repos/%s/%s/collaborators' % (
            user, project), params=payload)
        path = '/%s/%s/' % (user, project)
        project.collaborators.clear()
        UserPermission.objects.filter(path=path).delete()
        for data in collaborators:
            collaborator, created = User.objects.get_or_create(
                login=data['login'], id=data['id'])
            if collaborator == user:
                UserPermission.objects.create(
                    user=user, path=path, permission='admin')
            if created:
                user.is_active = False
                user.save()
            UserPermission.objects.create(
                user=collaborator, path=path, permission='read')
            project.collaborators.add(collaborator)
            logger.info('Added %s as a collaborator for %s' % (
                collaborator, project))
    logger.info('Collaborators have been synced for %s' % user)


@celery.task
def sync_org_repos_github(org, payload):
    """Syncs all the repositories of an organization with GitHub."""
    logger.info('Syncing organization repos for %s with GitHub' % org)
    repos = github_api_get('/orgs/%s/repos' % org, payload)
    for repo in repos:
        project = Project.from_kwargs(**repo)
        logger.info('Project %s has been synced' % project.name)
    logger.info('Organization repos have been synced for %s' % org)


@celery.task
def sync_org_members_github(org, payload):
    """Syncs the members of an organization with GitHub."""
    logger.info('Syncing organization members for %s with GitHub' % org)
    members = github_api_get('/orgs/%s/members' % org, params=payload)
    public_members = github_api_get('/orgs/%s/public_members' % org,
                                    params=payload)
    org.members.clear()
    org.public_members.clear()
    for data in members:
        user, created = User.objects.get_or_create(
            login=data['login'], id=data['id'])
        if created:
            # Then marks this user as being inactive
            user.is_active = False
            user.save()
        org.members.add(user)
        # Updates the public members list
        if data in public_members:
            org.public_members.add(user)
        logger.info('User %s has been added as member of %s' % (user, org))
    org.save()
    logger.info('Organization members have been synced for %s' % org)
    return org


@celery.task
def sync_org_teams_github(org, payload):
    """Syncs the teams for an organization with GitHub"""
    logger.info('Syncing organization teams for %s with GitHub' % org)
    teams = github_api_get('/orgs/%s/teams' % org, params=payload)
    for data in teams:
        team = Team.from_kwargs(organization=org, **data)
        # Sync team members and repos
        celery.chain(
            sync_team_members_github.s(team, payload),
            sync_team_repos_github.s(team, payload),
        ).apply_async()
        logger.info('Team %s has been synced' % team.id)
    logger.info('Organization teams have been synced for %s' % org)


@celery.task
def sync_team_members_github(team, payload):
    """Syncs a team's member list."""
    logger.info('Syncing members for team %s with GitHub' % team)
    members = github_api_get('/teams/%s/members' % team.id, params=payload)
    team.members.clear()
    for data in members:
        member = User.objects.get(id=data['id'])
        team.members.add(member)
        logger.info('Member %s has been added to team %s' % (member, team))
    team.save()
    logger.info('Members have been synced for team %s' % team)
    return team.organization


@celery.task
def sync_team_repos_github(org, team, payload):
    """Syncs a team's repository list."""
    logger.info('Syncing repos for team %s with GitHub' % team)
    repos = github_api_get('/teams/%s/repos' % team.id, params=payload)
    team.project_set.clear()
    for data in repos:
        project = Project.objects.get(owner=org, name=data['name'])
        project.teams.add(team)
        path = '/%s/%s/' % (org, project)
        GroupPermission.objects.filter(group=team, path=path).delete()
        if team.permission == 'admin':
            # Then adds admin permission as well as read permission
            GroupPermission.objects.create(
                group=team, path=path, permission=team.permission)
        GroupPermission.objects.create(
            group=team, path=path, permission='read')
        logger.info('Repo %s has been added to team %s' % (project, team))
    team.save()
    logger.info('Repos have been synced for team %s' % team)


def sync_user_account_github(user, payload):
    """Syncs a user account with GitHub."""
    sync_user_repos_github(user, payload)
    sync_user_collaborators_github.delay(user, payload)
    user.github_sync_date = datetime.datetime.utcnow().replace(tzinfo=utc)
    user.save()


def sync_org_account_github(org, payload):
    """Syncs an organization account with GitHub."""
    sync_org_repos_github(org, payload)
    celery.chain(
        sync_org_members_github.s(org, payload),
        sync_org_teams_github.s(payload),
    ).apply_async()
    org.github_sync_date = datetime.datetime.utcnow().replace(tzinfo=utc)
    org.save()
