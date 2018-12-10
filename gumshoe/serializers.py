from django.contrib.auth.models import User
from rest_framework import serializers

from gumshoe.fields import UnixtimeField, PkListField, PkField, IssueTypeField, PriorityField
from gumshoe.models import Version, Component, Priority, IssueType, Issue, Project, Milestone, Comment


class ComponentSerializer (serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="components_detail", lookup_field="pk")

    class Meta:
        model = Component
        fields = ('id', 'url', 'name', 'description')


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ('id', 'name', 'short_name', 'weight')


class VersionSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="versions_detail", lookup_field="pk")

    class Meta:
        model = Version
        fields = ('id', 'url', 'name', 'description')
        lookup_field = "versions_detail"


class ProjectSerializer (serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="project-detail", lookup_field="pk")
    components = ComponentSerializer(many=True, source="component_set", read_only=True)
    versions = VersionSerializer(many=True, source="version_set", read_only=True)
    priorities = serializers.SerializerMethodField()
    issue_types = serializers.SerializerMethodField()
    statuses = serializers.SerializerMethodField()
    resolutions = serializers.SerializerMethodField()

    def get_priorities(self, obj):
        return PrioritySerializer(list(Priority.objects.all()), many=True).data

    def get_issue_types(self, obj):
        return [issue_type.short_name for issue_type in IssueType.objects.all()]

    def get_resolutions(self, obj):
        return [resolution[0] for resolution in Issue.RESOLUTION_CHOICES]

    def get_statuses(self, obj):
        return [status[0] for status in Issue.STATUS_CHOICES]

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'description', 'issue_key', 'components', 'versions', 'priorities', 'issue_types', 'resolutions', 'statuses')


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ("id", "name", "description")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = ('id', 'username', 'first_name', 'last_name')


class CommentSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(view_name="comment-detail", lookup_field="pk")
    author = UserSerializer(read_only=True)
    created = UnixtimeField(read_only=True, millis=True)
    updated = UnixtimeField(read_only=True, millis=True)
    text = serializers.CharField(required=True)

    def _restore_comment(self, attrs, comment=None):
        comment.text = attrs.get("text")

        comment.save()

        return comment

    def create(self, validated_data):
        return self._restore_comment(validated_data, Comment())

    def update(self, instance, validated_data):
        return self._restore_comment(validated_data, instance)


class IssueSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk", required=False)
    url = serializers.HyperlinkedIdentityField(view_name="issue-detail", lookup_field="issue_key")
    summary = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    steps_to_reproduce = serializers.CharField(required=False, allow_blank=True)
    issue_key = serializers.CharField(read_only=True)
    components = PkListField(required=False)
    affects_versions = PkListField(required=False)
    fix_versions = PkListField(required=False)
    project = PkField()
    status = serializers.ChoiceField(choices=Issue.STATUS_CHOICES)
    resolution = serializers.ChoiceField(choices=Issue.RESOLUTION_CHOICES)
    issue_type = IssueTypeField()
    priority = PriorityField()
    assignee_id = PkField(required=False, write_only=True, allow_null=True)
    assignee = UserSerializer(required=False, allow_null=True)
    reporter = UserSerializer(read_only=True)
    reported = UnixtimeField(millis=True, read_only=True)
    last_updated = UnixtimeField(millis=True, read_only=True)

    milestone_id = PkField(required=False, write_only=True, allow_null=True)
    milestone = MilestoneSerializer(required=False, read_only=True)

    comments_url = serializers.SerializerMethodField()

    def _restore_issue(self, attrs, issue=None):
        issue.summary = attrs.get("summary") or issue.summary
        issue.description = attrs.get("description") or issue.description
        issue.steps_to_reproduce = attrs.get("steps_to_reproduce") or issue.steps_to_reproduce
        issue.project = Project.objects.get(pk=attrs.get("project"))
        issue.issue_type = attrs.get("issue_type")
        issue.priority = attrs.get("priority")

        milestone_id = attrs.get("milestone_id")
        if milestone_id:
            issue.milestone = Milestone.objects.get(pk=milestone_id)
        else:
            issue.milestone = None

        issue.status = attrs.get("status") or issue.status
        issue.resolution = attrs.get("resolution") or issue.resolution

        if attrs.get("assignee_id"):
            issue.assignee = User.objects.get(pk=attrs["assignee_id"])

        issue.components_detached = issue.project.component_set.filter(pk__in=attrs.get("components"))
        issue.affects_versions_detached = issue.project.version_set.filter(pk__in=attrs.get("affects_versions"))
        issue.fix_versions_detached = issue.project.version_set.filter(pk__in=attrs.get("fix_versions"))

        issue.save()

        return issue

    def get_comments_url(self, obj):
        return f"http://localhost:9123/rest/issues/{obj.issue_key}/comments/"

    def create(self, validated_data):
        return self._restore_issue(validated_data, Issue())

    def update(self, instance, validated_data):
        return self._restore_issue(validated_data, instance)
