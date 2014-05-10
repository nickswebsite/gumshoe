# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Comment'
        db.create_table(u'gumshoe_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'gumshoe', ['Comment'])

        # Adding model 'Project'
        db.create_table(u'gumshoe_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('issue_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
        ))
        db.send_create_signal(u'gumshoe', ['Project'])

        # Adding model 'Component'
        db.create_table(u'gumshoe_component', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.Project'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'gumshoe', ['Component'])

        # Adding unique constraint on 'Component', fields ['project', 'name']
        db.create_unique(u'gumshoe_component', ['project_id', 'name'])

        # Adding model 'Version'
        db.create_table(u'gumshoe_version', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.Project'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'gumshoe', ['Version'])

        # Adding unique constraint on 'Version', fields ['project', 'name']
        db.create_unique(u'gumshoe_version', ['project_id', 'name'])

        # Adding model 'Milestone'
        db.create_table(u'gumshoe_milestone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'gumshoe', ['Milestone'])

        # Adding model 'Priority'
        db.create_table(u'gumshoe_priority', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=4)),
        ))
        db.send_create_signal(u'gumshoe', ['Priority'])

        # Adding model 'IssueType'
        db.create_table(u'gumshoe_issuetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('icon', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'gumshoe', ['IssueType'])

        # Adding model 'Issue'
        db.create_table(u'gumshoe_issue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('issue_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.IssueType'], on_delete=models.PROTECT)),
            ('priority', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.Priority'], on_delete=models.PROTECT)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.Project'], on_delete=models.PROTECT)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('steps_to_reproduce', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('issue_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('assignee', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='issues_assigned', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('reporter', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='issues_reported', null=True, on_delete=models.PROTECT, to=orm['auth.User'])),
            ('reported', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gumshoe.Milestone'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='OPEN', max_length=32)),
            ('resolution', self.gf('django.db.models.fields.CharField')(default='UNRESOLVED', max_length=32)),
        ))
        db.send_create_signal(u'gumshoe', ['Issue'])

        # Adding M2M table for field components on 'Issue'
        m2m_table_name = db.shorten_name(u'gumshoe_issue_components')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('issue', models.ForeignKey(orm[u'gumshoe.issue'], null=False)),
            ('component', models.ForeignKey(orm[u'gumshoe.component'], null=False))
        ))
        db.create_unique(m2m_table_name, ['issue_id', 'component_id'])

        # Adding M2M table for field affects_versions on 'Issue'
        m2m_table_name = db.shorten_name(u'gumshoe_issue_affects_versions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('issue', models.ForeignKey(orm[u'gumshoe.issue'], null=False)),
            ('version', models.ForeignKey(orm[u'gumshoe.version'], null=False))
        ))
        db.create_unique(m2m_table_name, ['issue_id', 'version_id'])

        # Adding M2M table for field fix_versions on 'Issue'
        m2m_table_name = db.shorten_name(u'gumshoe_issue_fix_versions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('issue', models.ForeignKey(orm[u'gumshoe.issue'], null=False)),
            ('version', models.ForeignKey(orm[u'gumshoe.version'], null=False))
        ))
        db.create_unique(m2m_table_name, ['issue_id', 'version_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Version', fields ['project', 'name']
        db.delete_unique(u'gumshoe_version', ['project_id', 'name'])

        # Removing unique constraint on 'Component', fields ['project', 'name']
        db.delete_unique(u'gumshoe_component', ['project_id', 'name'])

        # Deleting model 'Comment'
        db.delete_table(u'gumshoe_comment')

        # Deleting model 'Project'
        db.delete_table(u'gumshoe_project')

        # Deleting model 'Component'
        db.delete_table(u'gumshoe_component')

        # Deleting model 'Version'
        db.delete_table(u'gumshoe_version')

        # Deleting model 'Milestone'
        db.delete_table(u'gumshoe_milestone')

        # Deleting model 'Priority'
        db.delete_table(u'gumshoe_priority')

        # Deleting model 'IssueType'
        db.delete_table(u'gumshoe_issuetype')

        # Deleting model 'Issue'
        db.delete_table(u'gumshoe_issue')

        # Removing M2M table for field components on 'Issue'
        db.delete_table(db.shorten_name(u'gumshoe_issue_components'))

        # Removing M2M table for field affects_versions on 'Issue'
        db.delete_table(db.shorten_name(u'gumshoe_issue_affects_versions'))

        # Removing M2M table for field fix_versions on 'Issue'
        db.delete_table(db.shorten_name(u'gumshoe_issue_fix_versions'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'gumshoe.comment': {
            'Meta': {'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'gumshoe.component': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Component'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.Project']"})
        },
        u'gumshoe.issue': {
            'Meta': {'object_name': 'Issue'},
            'affects_versions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'issues'", 'blank': 'True', 'to': u"orm['gumshoe.Version']"}),
            'assignee': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'issues_assigned'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'components': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['gumshoe.Component']", 'symmetrical': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fix_versions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'issues_to_fix'", 'blank': 'True', 'to': u"orm['gumshoe.Version']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'issue_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.IssueType']", 'on_delete': 'models.PROTECT'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.Milestone']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.Priority']", 'on_delete': 'models.PROTECT'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.Project']", 'on_delete': 'models.PROTECT'}),
            'reported': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'issues_reported'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['auth.User']"}),
            'resolution': ('django.db.models.fields.CharField', [], {'default': "'UNRESOLVED'", 'max_length': '32'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'OPEN'", 'max_length': '32'}),
            'steps_to_reproduce': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        },
        u'gumshoe.issuetype': {
            'Meta': {'object_name': 'IssueType'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'icon': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        u'gumshoe.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'gumshoe.priority': {
            'Meta': {'ordering': "('-weight',)", 'object_name': 'Priority'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'weight': ('django.db.models.fields.IntegerField', [], {})
        },
        u'gumshoe.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'gumshoe.version': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Version'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gumshoe.Project']"})
        }
    }

    complete_apps = ['gumshoe']