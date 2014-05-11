import datetime
import time

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from rest_framework.decorators import api_view, link, action
from rest_framework.pagination import PaginationSerializer
from rest_framework.response import Response
from rest_framework.reverse import reverse

from gumshoe.models import Project, IssueType, Issue, Priority, Component, Version, Milestone, Comment


def now():
    return datetime.datetime.utcnow()

def test_view(request):
    return render(request, "base.html")

@login_required()
def index(request):
    return HttpResponseRedirect(reverse('issues_list_form'))

def login(request):
    context_dict = {}
    if request.method == "GET":
        if request.user.is_authenticated():
            return HttpResponseRedirect("/")

    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect("/")

        context_dict["error_message"] = "Invalid login credentials"

    return render(request, "gumshoe/login.html", context_dict)

@login_required
def issue_form(request, issue_key=None):
    return render(request, "gumshoe/update-issue.html")

@login_required
def issue_list_view(request):
    return render(request, "gumshoe/issue-list.html")

@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/login/")

@login_required
def tests_view(request):
    app_scripts = [
        "gumshoe.js"
    ]

    test_scripts = [
        "test.url.js"
    ]

    ctx = {
        "scripts": ["js/{0}".format(s) for s in app_scripts] + ["js/{0}".format(s) for s in test_scripts]
    }

    return render(request, "tests/test-main.html", ctx)


from rest_framework import generics, serializers, viewsets, routers, renderers, parsers

@api_view(['GET'])
def api_root(request, format=None):
    """
    Doc string for api_root
    """
    return Response({
        "projects": reverse('projects_list', request=request, format=format),
    })

class VersionSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="versions_detail", lookup_field="pk")
    class Meta:
        model = Version
        fields = ('id', 'url', 'name', 'description')
        lookup_field = "versions_detail"

class ComponentSerializer (serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="components_detail", lookup_field="pk")
    class Meta:
        model = Component
        fields = ('id', 'url', 'name', 'description')

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ('id', 'name', 'short_name', 'weight')

class ProjectSerializer (serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="project-detail", lookup_field="pk")
    components = ComponentSerializer(many=True, source="component_set", read_only=True)
    versions = VersionSerializer(many=True, source="version_set", read_only=True)
    priorities = serializers.SerializerMethodField("get_priorities")
    issue_types = serializers.SerializerMethodField("get_issue_types")
    statuses = serializers.SerializerMethodField("get_statuses")
    resolutions = serializers.SerializerMethodField("get_resolutions")

    def get_priorities(self, obj):
        return PrioritySerializer(list(Priority.objects.all())).data

    def get_issue_types(self, obj):
        return [issue_type.short_name for issue_type in IssueType.objects.all()]

    def get_resolutions(self, obj):
        return [resolution[0] for resolution in Issue.RESOLUTION_CHOICES]

    def get_statuses(self, obj):
        return [status[0] for status in Issue.STATUS_CHOICES]

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'description', 'issue_key', 'components', 'versions', 'priorities', 'issue_types', 'resolutions', 'statuses')

class PkListField(serializers.WritableField):
    def to_native(self, obj):
        if hasattr(obj, "all"):
            return [o.pk for o in obj.all()]
        else:
            return [o.pk for o in obj]

    def from_native(self, value):
        if isinstance(value, list):
            return value
        else:
            msg = self.error_messages["invalid"]
            raise ValidationError(msg)

class PkField(serializers.WritableField):
    def to_native(self, obj):
        if obj is not None:
            return obj.pk
        return None

    def from_native(self, value):
        if isinstance(value, long) or isinstance(value, int) or value is None:
            return value
        msg = self.error_messages["invalid"]
        raise ValidationError(msg)

class ShortNameField(serializers.WritableField):
    def to_native(self, obj):
        return obj.short_name

    def from_native(self, value):
        if not isinstance(value, basestring):
            raise ValidationError(self.error_messages["invalid"])

        try:
            return self.model.objects.get(short_name=value)
        except IssueType.DoesNotExist:
            raise ValidationError(self.error_messages["invalid"])

class IssueTypeField(ShortNameField):
    model = IssueType

class PriorityField(ShortNameField):
    model = Priority

class UnixtimeField(serializers.DateTimeField):
    def __init__(self, *args, **kwds):
        is_java_time = kwds.pop("millis", False)
        if is_java_time:
            self.scaling = 1000
        else:
            self.scaling = 1

        super(UnixtimeField, self).__init__(*args, **kwds)

    def to_native(self, value):
        return int(time.mktime(value.timetuple())) * self.scaling

    def from_native(self, value):
        return datetime.datetime.fromtimestamp(int(value) / self.scaling)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = ('id', 'username', 'first_name', 'last_name')

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ("id", "name", "description")

class CommentSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk", required=False)
    author = UserSerializer(read_only=True)
    created = UnixtimeField(read_only=True, millis=True)
    updated = UnixtimeField(read_only=True, millis=True)
    text = serializers.CharField(required=True)

    def restore_object(self, attrs, instance=None):
        instance = instance or Comment()
        instance.text = attrs.get("text")
        instance.pk = attrs.get("pk")
        return instance

class IssueSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk", required=False)
    url = serializers.HyperlinkedIdentityField(view_name="issue-detail", lookup_field="issue_key")
    summary = serializers.CharField()
    description = serializers.CharField(required=False)
    steps_to_reproduce = serializers.CharField(required=False)
    issue_key = serializers.CharField(read_only=True)
    components = PkListField(required=False)
    affects_versions = PkListField(required=False)
    fix_versions = PkListField(required=False)
    project = PkField()
    status = serializers.ChoiceField(choices=Issue.STATUS_CHOICES)
    resolution = serializers.ChoiceField(choices=Issue.RESOLUTION_CHOICES)
    issue_type = IssueTypeField()
    priority = PriorityField()
    assignee_id = PkField(required=False, write_only=True)
    assignee = UserSerializer(required=False)
    reporter = UserSerializer(read_only=True)
    reported = UnixtimeField(millis=True, read_only=True)
    last_updated = UnixtimeField(millis=True, read_only=True)

    milestone_id = PkField(required=False, write_only=True)
    milestone = MilestoneSerializer(required=False, read_only=True)

    def restore_object(self, attrs, instance=None):
        issue = instance or Issue()
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

        return issue

class IssuePaginatinationSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = IssueSerializer

def get_pk_list(pk_str):
    return [int(pk) for pk in pk_str.split(",")]

class IssueViewSet(viewsets.ViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    base_name = "issues"
    lookup_field = "issue_key"

    def list(self, request):
        page_size = request.GET.get("page_size", 25)
        page = request.GET.get("page", 1)

        projects_param = request.GET.get("projects")
        statuses_param = request.GET.get("statuses")
        fix_versions_param = request.GET.get("fix_versions")
        affects_versions_param = request.GET.get("affects_versions")
        assignees_param = request.GET.get("assignees")
        milestones_param = request.GET.get("milestones")
        terms_param = request.GET.get("terms")

        order_by_param = request.GET.get("order_by")

        no_affects_version = False
        no_fix_version = False
        unassigned = False

        q = {}
        if projects_param:
            q["project__issue_key__in"] = projects_param.split(",")
        if statuses_param:
            q["status__in"] = statuses_param.split(",")
        if fix_versions_param:
            fix_version_pks = get_pk_list(fix_versions_param)
            if -1 in fix_version_pks:
                no_fix_version = True
                fix_version_pks.remove(-1)
            q["fix_versions__pk__in"] = fix_version_pks
        if affects_versions_param:
            affects_version_pks = get_pk_list(affects_versions_param)
            if -1 in affects_version_pks:
                no_affects_version = True
                affects_version_pks.remove(-1)
            q["affects_versions__pk__in"] = affects_version_pks
        if assignees_param:
            assignee_pks = get_pk_list(assignees_param)
            if -1 in assignee_pks:
                unassigned = True
                assignee_pks.remove(-1)
            q["assignee__pk__in"] = assignee_pks
        if milestones_param:
            milestone_pks = get_pk_list(milestones_param)
            if -1 in milestone_pks:
                no_milestone = True
                milestone_pks.remove(-1)
            q["milestone__pk__in"] = milestone_pks

        query = Q(**q)
        if terms_param:
            query = query & (Q(summary__contains=terms_param) | Q(description__contains=terms_param) | Q(issue_key=terms_param))

        qs = Issue.objects.filter(query)
        if no_fix_version:
            qs |= Issue.objects.filter(fix_versions=None)
        if no_affects_version:
            qs |= Issue.objects.filter(affects_version=None)
        if unassigned:
            qs |= Issue.objects.filter(assignee=None)

        if order_by_param is not None:
            order_by_fields = order_by_param.split(",")
            qs = qs.order_by(*order_by_fields)

        paginator = Paginator(qs, page_size)

        try:
            res = paginator.page(page)
        except PageNotAnInteger:
            res = paginator.page(1)
        except EmptyPage:
            res = paginator.page(paginator.num_pages)

        serializer = IssuePaginatinationSerializer(res, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.DATA, context={"request": request})
        if serializer.is_valid():
            issue = serializer.object
            issue.reporter = request.user
            issue.assignee = issue.assignee or issue.reporter
            issue.save()

            if hasattr(issue, "components_detached"):
                issue.components = issue.components_detached
            if hasattr(issue, "affects_versions_detached"):
                issue.affects_versions = issue.affects_versions_detached
            if hasattr(issue, "fix_versions_detached"):
                issue.fix_versions = issue.fix_versions_detached

            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, issue_key=None):
        try:
            issue = Issue.objects.get(issue_key=issue_key)
        except Issue.DoesNotExist:
            raise Http404

        serializer = self.serializer_class(issue, context={"request": request})
        return Response(serializer.data, status=200)

    @action(methods=["get", "put", "post"])
    def comments(self, request, issue_key=None):
        try:
            issue = Issue.objects.get(issue_key=issue_key)
        except Issue.DoesNotExist:
            raise Http404

        if request.method == "GET":
            serializer = CommentSerializer(issue.comments.all(), many=True)
            return Response(serializer.data, status=200)
        elif request.method == "POST":
            serializer = CommentSerializer(data=request.DATA, context={"request": request})
            if serializer.is_valid():
                comment = serializer.object
                comment.content = issue
                comment.author = request.user
                comment.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=400)
        elif request.method == "PUT":
            serializer = CommentSerializer(data=request.DATA, context={"request": request})
            if serializer.is_valid():
                comment_detached = serializer.object
                comment = Comment.objects.get(pk=comment_detached.pk)
                comment.text = comment_detached.text
                comment.save()
                return Response(CommentSerializer(comment, context={"request": request}).data, status=200)
            return Response(serializer.errors, status=400)

    def update(self, request, issue_key=None):
        try:
            issue = Issue.objects.get(issue_key=issue_key)
        except Issue.DoesNotExist:
            raise Http404

        serializer = self.serializer_class(data=request.DATA, context={"request": request})
        if serializer.is_valid():
            issue_detached = serializer.object
            issue_detached.issue_key = issue_key

            issue.issue_type = issue_detached.issue_type
            issue.summary = issue_detached.summary
            issue.description = issue_detached.description
            issue.steps_to_reproduce = issue_detached.steps_to_reproduce
            issue.priority = issue_detached.priority
            issue.status = issue_detached.status
            issue.resolution = issue_detached.resolution
            issue.milestone = issue_detached.milestone
            issue.assignee = issue_detached.assignee or request.user
            if hasattr(issue_detached, "components_detached"):
                issue.components = issue_detached.components_detached
            if hasattr(issue_detached, "affects_versions_detached"):
                issue.affects_versions = issue_detached.affects_versions_detached
            if hasattr(issue_detached, "fix_versions_detached"):
                issue.fix_versions = issue_detached.fix_versions_detached

            issue.save()
            return Response(self.serializer_class(issue, context={"request": request}).data, status=200)
        return Response(serializer.errors, status=400)

class VersionDetailView (generics.RetrieveAPIView):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer

class ComponentDetailView (generics.RetrieveUpdateAPIView):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Doc string for ProjectViewSet
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    base_name = "projects"

class UsersViewSet (viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    base_name = "users"

class MilestoneViewSet (viewsets.ReadOnlyModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    base_name = "milestones"

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'issues', IssueViewSet)
router.register(r'users', UsersViewSet)
router.register(r'milestones', MilestoneViewSet)

@login_required()
def settings_view(request):
    if request.method == "PUT":
        request.session["settings"] = request.body
    res = request.session.get("settings", '{"unsaved": true}')
    return HttpResponse(res, content_type="application/json", status=200)

@api_view(["GET"])
def pages_view(request):
    return Response({
        "issues_add": reverse('issues_add_form'),
        "issues": reverse('issues_list_form'),
        "user_home": reverse('issues_list_form'),
    })
