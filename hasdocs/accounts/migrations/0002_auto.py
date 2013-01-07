# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field public_members on 'Organization'
        db.create_table('accounts_organization_public_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['accounts.organization'], null=False)),
            ('user', models.ForeignKey(orm['accounts.user'], null=False))
        ))
        db.create_unique('accounts_organization_public_members', ['organization_id', 'user_id'])


    def backwards(self, orm):
        # Removing M2M table for field public_members on 'Organization'
        db.delete_table('accounts_organization_public_members')


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
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['accounts.User']", 'null': 'True', 'blank': 'True'}),
            'public_members': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'public_organization_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.User']"})
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