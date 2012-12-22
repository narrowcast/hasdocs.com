# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Generator'
        db.create_table('projects_generator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('projects', ['Generator'])

        # Adding model 'Language'
        db.create_table('projects_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('projects', ['Language'])

        # Adding model 'Project'
        db.create_table('projects_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.BaseUser'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('private', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('html_url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200, blank=True)),
            ('git_url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Language'], null=True, blank=True)),
            ('generator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Generator'], null=True, blank=True)),
            ('requirements_path', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('docs_path', self.gf('django.db.models.fields.CharField')(default='docs', max_length=200)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('mod_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('projects', ['Project'])

        # Adding M2M table for field collaborators on 'Project'
        db.create_table('projects_project_collaborators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['projects.project'], null=False)),
            ('user', models.ForeignKey(orm['accounts.user'], null=False))
        ))
        db.create_unique('projects_project_collaborators', ['project_id', 'user_id'])

        # Adding M2M table for field teams on 'Project'
        db.create_table('projects_project_teams', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['projects.project'], null=False)),
            ('team', models.ForeignKey(orm['accounts.team'], null=False))
        ))
        db.create_unique('projects_project_teams', ['project_id', 'team_id'])

        # Adding model 'Build'
        db.create_table('projects_build', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('output', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('finished_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('projects', ['Build'])

        # Adding model 'Domain'
        db.create_table('projects_domain', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projects.Project'])),
        ))
        db.send_create_signal('projects', ['Domain'])


    def backwards(self, orm):
        # Deleting model 'Generator'
        db.delete_table('projects_generator')

        # Deleting model 'Language'
        db.delete_table('projects_language')

        # Deleting model 'Project'
        db.delete_table('projects_project')

        # Removing M2M table for field collaborators on 'Project'
        db.delete_table('projects_project_collaborators')

        # Removing M2M table for field teams on 'Project'
        db.delete_table('projects_project_teams')

        # Deleting model 'Build'
        db.delete_table('projects_build')

        # Deleting model 'Domain'
        db.delete_table('projects_domain')


    models = {
        'accounts.baseuser': {
            'Meta': {'object_name': 'BaseUser'},
            'blog': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'github_sync_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gravatar_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Plan']", 'null': 'True', 'blank': 'True'})
        },
        'accounts.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['accounts.BaseUser']},
            'baseuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.BaseUser']", 'unique': 'True', 'primary_key': 'True'}),
            'billing_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['accounts.User']", 'null': 'True', 'blank': 'True'})
        },
        'accounts.plan': {
            'Meta': {'object_name': 'Plan'},
            'business': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'price': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '64', 'decimal_places': '2'}),
            'private_docs': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'accounts.team': {
            'Meta': {'unique_together': "(('name', 'organization'),)", 'object_name': 'Team'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['accounts.User']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Organization']"}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '5'})
        },
        'accounts.user': {
            'Meta': {'object_name': 'User', '_ormbases': ['accounts.BaseUser']},
            'baseuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.BaseUser']", 'unique': 'True', 'primary_key': 'True'}),
            'github_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'heroku_api_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'projects.build': {
            'Meta': {'ordering': "['-started_at']", 'object_name': 'Build'},
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'output': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']"}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'projects.domain': {
            'Meta': {'object_name': 'Domain'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']"})
        },
        'projects.generator': {
            'Meta': {'object_name': 'Generator'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'projects.language': {
            'Meta': {'object_name': 'Language'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'projects.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'collaborating_project_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'docs_path': ('django.db.models.fields.CharField', [], {'default': "'docs'", 'max_length': '200'}),
            'generator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Generator']", 'null': 'True', 'blank': 'True'}),
            'git_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'html_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Language']", 'null': 'True', 'blank': 'True'}),
            'mod_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.BaseUser']"}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'requirements_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'teams': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['accounts.Team']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['projects']