import random
import string

from django.contrib.auth.models import User

from gumshoe.models import Comment, Component, Issue, IssueType, Milestone, Priority, Project, Version


def random_string(max_length=255):
    return "".join([random.choice(string.ascii_letters + string.digits + "_-!@#$%^&*()+=\t ,.<>/?[]{}\\|'\";:`~") for _ in range(max_length)])


def random_priority():
    return random.choice(list(Priority.objects.all())).short_name


def random_status():
    return random.choice(Issue.STATUS_CHOICES)[0]


def random_resolution():
    return random.choice(Issue.RESOLUTION_CHOICES)[0]


def random_issue_type():
    return random.choice(list(IssueType.objects.all())).short_name


class IssueTestCaseBase(object):
    def setUpProject(self):
        self.user = User.objects.create_user("testuser", "", "password")
        self.another_user = User.objects.create_user("another_user", "", "password")

        login_result = self.client.login(username="testuser", password="password")
        assert login_result

        self.project = Project(name="Test Project", issue_key="TESTPROJECT")
        self.project.save()

        self.component_one = Component(name="Component One", project=self.project)
        self.component_one.save()

        self.component_two = Component(name="Component Two", project=self.project)
        self.component_two.save()

        self.version_one = Version(name="Version 1", project=self.project)
        self.version_one.save()

        self.version_two = Version(name="Version 2", project=self.project)
        self.version_two.save()

        self.milestone = Milestone(name="New Milestone")
        self.milestone.save()

    def assertAllEqual(self, cmp, *args):
        for arg in args:
            self.assertEqual(cmp, arg)

    def generate_issue(self, **kwds):
        issue = Issue()
        issue.project = kwds.get("project", self.project)
        issue.summary = kwds.get("summary", random_string(32))
        issue.description = kwds.get("description", random_string())
        issue.steps_to_reproduce = kwds.get("steps_to_reproduce", random_string())
        issue.priority = Priority.objects.get(short_name=kwds.get("priority", random_priority()))
        issue.issue_type = IssueType.objects.get(short_name=kwds.get("issue_type", random_issue_type()))
        issue.status = kwds.get("status", random_status())
        issue.resolution = kwds.get("resolution", random_resolution())
        if issue.status == "OPEN" and not "resolution" in kwds:
            issue.resolution = Issue.RESOLUTION_CHOICES[0][0]
        issue.milestone = kwds.get("milestone", self.milestone)
        issue.reporter = kwds.get("reporter", self.user)
        issue.assignee = kwds.get("assignee", self.user)
        issue.save()

        issue.components.set(kwds.get("components", [self.component_two]))
        issue.affects_versions.set(kwds.get("affects_versions", [self.version_one]))
        issue.fix_versions.set(kwds.get("fix_versions", [self.version_one]))

        return issue

    def generate_comment(self, issue, **kwds):
        comment = Comment()
        comment.content = issue
        comment.text = kwds.get("text", random_string())
        comment.author = kwds.get("author", self.user)
        comment.save()

        return comment
