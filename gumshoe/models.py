import datetime

from django.utils.timezone import utc
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class Comment(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    author = models.ForeignKey(User)
    created = models.DateTimeField(null=False)
    updated = models.DateTimeField(null=False)
    text = models.TextField()

    def __str__(self):
        return self.text

    def save(self, *args, **kwds):
        if kwds.pop("update_timestamps", True):
            if self.pk is None:
                self.created = datetime.datetime.utcnow().replace(tzinfo=utc)
            self.updated = datetime.datetime.utcnow().replace(tzinfo=utc)
        super(Comment, self).save(*args, **kwds)


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=False)
    issue_key = models.CharField(max_length=16, unique=True)

    def next_issue_key(self):
        return "{0}-{1}".format(self.issue_key, self.issue_set.count() + 1)

    def __str__(self):
        return self.name

class Component(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=False)

    class Meta:
        unique_together = (('project', 'name'), )

    def __str__(self):
        return self.name + " (" + str(self.project) + ")"

class Version(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=False)

    class Meta:
        unique_together = (('project', 'name'), )

    def __str__(self):
        return "{0} : {1}".format(self.project, self.name)

class Milestone(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=False)

    def __str__(self):
        return self.name

class Priority(models.Model):
    weight = models.IntegerField()
    name = models.CharField(max_length=32)
    short_name = models.CharField(max_length=4)

    class Meta:
        ordering = ('-weight', )

    def __str__(self):
        return self.name

class IssueType(models.Model):
    name = models.CharField(max_length=32)
    description = models.TextField()
    short_name = models.CharField(max_length=8)
    icon = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class Issue(models.Model):
    RESOLUTION_CHOICES = (
        ('UNRESOLVED', 'Unresolved'),
        ('FIXED', 'Fixed'),
        ('WONT_FIX', "Won't Fix"),
        ("INVALID", "Invalid"),
    )

    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    )

    summary = models.CharField(max_length=2048)
    issue_type = models.ForeignKey(IssueType, on_delete=models.PROTECT)
    priority = models.ForeignKey(Priority, on_delete=models.PROTECT)

    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    description = models.TextField(blank=True)
    steps_to_reproduce = models.TextField(blank=True)

    issue_key = models.CharField(max_length=32, unique=True)

    assignee = models.ForeignKey(User, related_name='issues_assigned', blank=True, null=True, on_delete=models.SET_NULL)
    reporter = models.ForeignKey(User, related_name='issues_reported', blank=True, null=True, on_delete=models.PROTECT)
    reported = models.DateTimeField(blank=True, null=False)
    last_updated = models.DateTimeField(blank=True, null=False)

    components = models.ManyToManyField(Component, blank=True)
    affects_versions = models.ManyToManyField(Version, related_name='issues', blank=True)
    fix_versions = models.ManyToManyField(Version, related_name='issues_to_fix', blank=True)

    milestone = models.ForeignKey(Milestone, null=True, blank=True, on_delete=models.SET_NULL)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='OPEN')
    resolution = models.CharField(max_length=32, choices=RESOLUTION_CHOICES, default='UNRESOLVED')

    comments = GenericRelation(Comment)

    def __str__(self):
        return "{0} - {1}".format(self.issue_key, self.summary)

    def full_clean(self, exclude=None, validate_unique=True):
        exclude = exclude or []
        exclude += ["issue_key"]
        super(Issue, self).full_clean(exclude, validate_unique)

    def save(self, *args, **kwds):
        if self.issue_key is None or self.issue_key == "":
            self.issue_key = self.project.next_issue_key()

        if kwds.pop("update_timestamps", True):
            if self.pk is None:
                self.reported = datetime.datetime.utcnow().replace(tzinfo=utc)
            self.last_updated = datetime.datetime.utcnow().replace(tzinfo=utc)

        return super(Issue, self).save(*args, **kwds)

def issue_update_timestamp(*args, **kwds):
    if kwds.get("action") in {"post_add", "post_remove", "post_clear"}:
        kwds["instance"].save()

m2m_changed.connect(issue_update_timestamp, dispatch_uid="gumshoe.models.issue_update_timestamp")
