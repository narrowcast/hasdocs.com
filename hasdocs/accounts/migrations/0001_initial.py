# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Plan'
        db.create_table('accounts_plan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('private_docs', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('price', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=64, decimal_places=2)),
            ('business', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('accounts', ['Plan'])

        # Adding model 'AnonymousUser'
        db.create_table('accounts_anonymoususer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('accounts', ['AnonymousUser'])

        # Adding model 'BaseUser'
        db.create_table('accounts_baseuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('login', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('gravatar_id', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('blog', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Plan'], null=True, blank=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('github_sync_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['BaseUser'])

        # Adding model 'User'
        db.create_table('accounts_user', (
            ('baseuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.BaseUser'], unique=True, primary_key=True)),
            ('github_access_token', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('heroku_api_key', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('accounts', ['User'])

        # Adding model 'Organization'
        db.create_table('accounts_organization', (
            ('baseuser_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['accounts.BaseUser'], unique=True, primary_key=True)),
            ('billing_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('accounts', ['Organization'])

        # Adding M2M table for field members on 'Organization'
        db.create_table('accounts_organization_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['accounts.organization'], null=False)),
            ('user', models.ForeignKey(orm['accounts.user'], null=False))
        ))
        db.create_unique('accounts_organization_members', ['organization_id', 'user_id'])

        # Adding model 'Team'
        db.create_table('accounts_team', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Organization'])),
            ('permission', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal('accounts', ['Team'])

        # Adding unique constraint on 'Team', fields ['name', 'organization']
        db.create_unique('accounts_team', ['name', 'organization_id'])

        # Adding M2M table for field members on 'Team'
        db.create_table('accounts_team_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['accounts.team'], null=False)),
            ('user', models.ForeignKey(orm['accounts.user'], null=False))
        ))
        db.create_unique('accounts_team_members', ['team_id', 'user_id'])

        # Adding model 'UserPermission'
        db.create_table('accounts_userpermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('permission', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'])),
        ))
        db.send_create_signal('accounts', ['UserPermission'])

        # Adding unique constraint on 'UserPermission', fields ['user', 'path', 'permission']
        db.create_unique('accounts_userpermission', ['user_id', 'path', 'permission'])

        # Adding model 'GroupPermission'
        db.create_table('accounts_grouppermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('permission', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Team'])),
        ))
        db.send_create_signal('accounts', ['GroupPermission'])

        # Adding unique constraint on 'GroupPermission', fields ['group', 'path', 'permission']
        db.create_unique('accounts_grouppermission', ['group_id', 'path', 'permission'])

        # Adding model 'OthersPermission'
        db.create_table('accounts_otherspermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('permission', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('accounts', ['OthersPermission'])

        # Adding unique constraint on 'OthersPermission', fields ['path', 'permission']
        db.create_unique('accounts_otherspermission', ['path', 'permission'])


    def backwards(self, orm):
        # Removing unique constraint on 'OthersPermission', fields ['path', 'permission']
        db.delete_unique('accounts_otherspermission', ['path', 'permission'])

        # Removing unique constraint on 'GroupPermission', fields ['group', 'path', 'permission']
        db.delete_unique('accounts_grouppermission', ['group_id', 'path', 'permission'])

        # Removing unique constraint on 'UserPermission', fields ['user', 'path', 'permission']
        db.delete_unique('accounts_userpermission', ['user_id', 'path', 'permission'])

        # Removing unique constraint on 'Team', fields ['name', 'organization']
        db.delete_unique('accounts_team', ['name', 'organization_id'])

        # Deleting model 'Plan'
        db.delete_table('accounts_plan')

        # Deleting model 'AnonymousUser'
        db.delete_table('accounts_anonymoususer')

        # Deleting model 'BaseUser'
        db.delete_table('accounts_baseuser')

        # Deleting model 'User'
        db.delete_table('accounts_user')

        # Deleting model 'Organization'
        db.delete_table('accounts_organization')

        # Removing M2M table for field members on 'Organization'
        db.delete_table('accounts_organization_members')

        # Deleting model 'Team'
        db.delete_table('accounts_team')

        # Removing M2M table for field members on 'Team'
        db.delete_table('accounts_team_members')

        # Deleting model 'UserPermission'
        db.delete_table('accounts_userpermission')

        # Deleting model 'GroupPermission'
        db.delete_table('accounts_grouppermission')

        # Deleting model 'OthersPermission'
        db.delete_table('accounts_otherspermission')


    models = {
        'accounts.anonymoususer': {
            'Meta': {'object_name': 'AnonymousUser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
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
        'accounts.grouppermission': {
            'Meta': {'unique_together': "(('group', 'path', 'permission'),)", 'object_name': 'GroupPermission'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Team']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'accounts.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['accounts.BaseUser']},
            'baseuser_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['accounts.BaseUser']", 'unique': 'True', 'primary_key': 'True'}),
            'billing_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['accounts.User']", 'null': 'True', 'blank': 'True'})
        },
        'accounts.otherspermission': {
            'Meta': {'unique_together': "(('path', 'permission'),)", 'object_name': 'OthersPermission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        'accounts.userpermission': {
            'Meta': {'unique_together': "(('user', 'path', 'permission'),)", 'object_name': 'UserPermission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.User']"})
        }
    }

    complete_apps = ['accounts']