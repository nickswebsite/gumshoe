from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.urls import reverse

from rest_framework import generics, viewsets, routers
from rest_framework.decorators import api_view, action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.reverse import reverse

from gumshoe.serializers import VersionSerializer, ComponentSerializer, ProjectSerializer, MilestoneSerializer, \
    CommentSerializer, UserSerializer, IssueSerializer
from gumshoe.models import Project, Issue, Component, Version, Milestone, Comment


#####################################
#  Entry point
#####################################

@login_required()
def index(request):
    return HttpResponseRedirect(reverse('issues_list_form'))


#####################################
#  Login and Logout
#####################################

def login(request):
    context_dict = {}
    if request.method == "GET":
        if request.user.is_authenticated:
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
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/login/")


#####################################
#  Angular Templates
#####################################

@login_required
def issue_form(request, issue_key=None):
    return render(request, "gumshoe/update-issue.html")


@login_required
def issue_list_view(request):
    return render(request, "gumshoe/issue-list.html")


#####################################
#  Testing stuff
#####################################

@login_required
def tests_view(request):
    app_scripts = [
        "gumshoe.js"
    ]

    test_scripts = [
        "test.url.js"
    ]

    ctx = {
        "scripts": [f"js/{s}" for s in app_scripts] + [f"js/{s}" for s in test_scripts]
    }

    return render(request, "tests/test-main.html", ctx)


#####################################
#  UI Support
#####################################

@login_required()
def settings_view(request):
    if request.method == "PUT":
        request.session["settings"] = request.body.decode()
    res = request.session.get("settings", '{"unsaved": true}')
    return HttpResponse(res, content_type="application/json", status=200)


#####################################
#  REST API
#####################################

@api_view(['GET'])
def api_root(request, format=None):
    """
    Doc string for api_root
    """
    return Response({
        "projects": reverse('projects_list', request=request, format=format),
    })


@api_view(["GET"])
def pages_view(request):
    return Response({
        "issues_add": reverse('issues_add_form'),
        "issues": reverse('issues_list_form'),
        "user_home": reverse('issues_list_form'),
    })


class ModelPaginationSerializer(object):
    serializer_class = None

    def __init__(self, request, queryset):
        self.queryset = queryset
        self.request = request

    def get_paginated_response(self):
        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(self.queryset, self.request)

        model_serializer = self.serializer_class(page, many=True, context={"request": self.request})

        return paginator.get_paginated_response(model_serializer.data)


class IssuePaginationSerializer(ModelPaginationSerializer):
    serializer_class = IssueSerializer


def get_pk_list(pk_str):
    return [int(pk) for pk in pk_str.split(",")]


class IssueViewSet(viewsets.ViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    base_name = "issues"
    lookup_field = "issue_key"

    def list(self, request):
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

        serializer = IssuePaginationSerializer(request, qs)
        return serializer.get_paginated_response()

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            issue = serializer.save()

            issue.reporter = request.user
            issue.assignee = issue.assignee or issue.reporter
            issue.save()

            if hasattr(issue, "components_detached"):
                issue.components.set(issue.components_detached)
            if hasattr(issue, "affects_versions_detached"):
                issue.affects_versions.set(issue.affects_versions_detached)
            if hasattr(issue, "fix_versions_detached"):
                issue.fix_versions.set(issue.fix_versions_detached)

            response_serializer = self.serializer_class(issue, context={"request": request})
            return Response(response_serializer.data, status=201)

        return Response(serializer.errors, status=400)

    def retrieve(self, request, issue_key=None):
        try:
            issue = Issue.objects.get(issue_key=issue_key)
        except Issue.DoesNotExist:
            raise Http404

        serializer = self.serializer_class(issue, context={"request": request})
        return Response(serializer.data, status=200)

    def update(self, request, issue_key=None):
        try:
            issue = Issue.objects.get(issue_key=issue_key)
        except Issue.DoesNotExist:
            raise Http404

        serializer = self.serializer_class(issue, data=request.data, context={"request": request})
        if serializer.is_valid():
            issue_detached = serializer.save()

            if hasattr(issue_detached, "components_detached"):
                issue.components.set(issue_detached.components_detached)
            if hasattr(issue_detached, "affects_versions_detached"):
                issue.affects_versions.set(issue_detached.affects_versions_detached)
            if hasattr(issue_detached, "fix_versions_detached"):
                issue.fix_versions.set(issue_detached.fix_versions_detached)

            issue.save()
            return Response(self.serializer_class(issue, context={"request": request}).data, status=200)
        return Response(serializer.errors, status=400)


class CommentCollectionView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        issue_key = None
        if "issue_key" in self.kwargs:
            issue_key = self.kwargs["issue_key"]

        if issue_key:
            issue = self.get_issue(issue_key)
            return issue.comments.all()

        return Comment.objects.none()

    def perform_create(self, serializer):
        # The issue is required for creating the comment and is NOT available
        # to the serializer, so we mimic what the serializer would do here.
        issue = self.get_issue(self.kwargs["issue_key"])

        comment = Comment()
        comment.text = serializer.validated_data["text"]
        comment.content = issue
        comment.author = self.request.user
        comment.save()

        serializer.instance = comment

    def get_issue(self, issue_key):
        return get_object_or_404(Issue, issue_key=issue_key)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class VersionDetailView(generics.RetrieveAPIView):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer


class ComponentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    base_name = "projects"


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    base_name = "users"


class MilestoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    base_name = "milestones"


router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'issues', IssueViewSet)
router.register(r'users', UsersViewSet)
router.register(r'milestones', MilestoneViewSet)
# router.register(r'comments', CommentsViewSets)
