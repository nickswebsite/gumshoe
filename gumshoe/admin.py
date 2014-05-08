from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericTabularInline

from django import forms
from gumshoe.models import Component, Issue, IssueType, Milestone, Priority, Project, Version, Comment


class IssueAdminForm (forms.ModelForm):
    class Meta:
        model = Issue

    reporter = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="Me", required=False)
    assignee = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="Auto Assign", required=False)

class CommentInline(GenericTabularInline):
    model = Comment
    extra = 0

class IssueModelAdmin (admin.ModelAdmin):
    readonly_fields = ('issue_key',)
    list_display = ('issue_type_short_name', 'issue_display', 'priority', 'resolution')
    list_display_links = ('issue_display',)

    form = IssueAdminForm

    def issue_type_short_name(self, obj):
        return obj.issue_type.short_name

    def issue_display(self, obj):
        return str(obj)

    list_filter = ('project', 'status', 'fix_versions')

    inlines = (CommentInline,)

    def save_model(self, request, obj, form, change):
        obj.reporter = obj.reporter or request.user
        obj.assignee = obj.reporter or request.user
        obj.save()

class ComponentInline (admin.StackedInline):
    model = Component
    extra = 0

class VersionInline (admin.StackedInline):
    model = Version
    extra = 0

class ProjectModelAdmin(admin.ModelAdmin):
    inlines = [VersionInline, ComponentInline]

# Register your models here.
admin.site.register(Issue, IssueModelAdmin)
admin.site.register(Project, ProjectModelAdmin)

admin.site.register((IssueType, Milestone, Priority))

