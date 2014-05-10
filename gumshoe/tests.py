import json
import string
import random

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase as TestCaseBase


# Create your tests here.
from gumshoe.models import Project, Priority, Component, Version, Issue, IssueType, Milestone, Comment


def random_string(max_length=255):
    return "".join([random.choice(string.ascii_letters + string.digits + "_-!@#$%^&*()+=\t ,.<>/?[]{}\\|'\";:`~") for _ in xrange(max_length)])

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

        self.client.login(username="testuser", password="password")

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

        issue.components = kwds.get("components", [self.component_two])
        issue.affects_versions = kwds.get("affects_versions", [self.version_one])
        issue.fix_versions = kwds.get("fix_versions", [self.version_one])

        return issue

    def generate_comment(self, issue, **kwds):
        comment = Comment()
        comment.content = issue
        comment.text = kwds.get("text", random_string())
        comment.author = kwds.get("author", self.user)
        comment.save()

        return comment

class IssuesApiTests (IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]
    NEW_ISSUES_ENDPOINT = "/rest/issues/"
    EXISTING_ISSUE_ENDPOINT = "/rest/issues/{0}/"

    def setUp(self):
        self.setUpProject()

    def test_new_issue(self):
        self.project.versions = [self.version_one, self.version_two]
        pl = {
            "project": self.project.pk,
            "issueKey": None,
            "issueType": random_issue_type(),
            "summary": random_string(),
            "description": random_string(),
            "stepsToReproduce": random_string(),
            "priority": random_priority(),
            "affectsVersions": [self.version_one.pk, self.version_two.pk],
            "fixVersions": [self.version_two.pk],
            "components": [self.component_one.pk, self.component_two.pk],
            "assigneeId": None,
            "status": random_status(),
            "resolution": random_resolution(),
            "milestoneId": self.milestone.pk,
        }

        if pl["status"] == "OPEN":
            pl["resolution"] = Issue.RESOLUTION_CHOICES[0][0]

        res = self.client.post(self.NEW_ISSUES_ENDPOINT, json.dumps(pl), content_type="application/json")
        self.assertEqual(201, res.status_code, res.data)
        res = json.loads(res.content)

        self.assertEqual(1, Issue.objects.count())
        issue = Issue.objects.get(pk=1)

        self.assertAllEqual(self.project.pk, res["project"], issue.project.pk)
        self.assertAllEqual(self.project.issue_key + "-1", res["issueKey"], issue.issue_key)
        self.assertAllEqual(pl["issueType"], res["issueType"], issue.issue_type.short_name)
        self.assertAllEqual(pl["summary"], res["summary"], issue.summary)
        self.assertAllEqual(pl["description"], res["description"], issue.description)
        self.assertAllEqual(pl["stepsToReproduce"], res["stepsToReproduce"], issue.steps_to_reproduce)
        self.assertAllEqual(pl["priority"], res["priority"], issue.priority.short_name)
        self.assertAllEqual(pl["status"], res["status"], issue.status)
        self.assertAllEqual(pl["resolution"], res["resolution"], issue.resolution)
        self.assertAllEqual(self.user.pk, res["reporter"]["id"], issue.reporter.pk)
        self.assertAllEqual(self.user.pk, res["assignee"]["id"], issue.assignee.pk)
        self.assertSetEqual(set(pl["components"]), {c.pk for c in issue.components.all()})
        self.assertSetEqual(set(pl["components"]), set(res["components"]))
        self.assertSetEqual(set(pl["affectsVersions"]), {v.pk for v in issue.affects_versions.all()})
        self.assertSetEqual(set(pl["affectsVersions"]), set(res["affectsVersions"]))
        self.assertSetEqual(set(pl["fixVersions"]), {v.pk for v in issue.fix_versions.all()})
        self.assertSetEqual(set(pl["fixVersions"]), set(res["fixVersions"]))
        self.assertAllEqual(self.milestone.pk, res["milestone"]["id"], issue.milestone.pk)

    def test_get_issue(self):
        issue = self.generate_issue()

        res = self.client.get(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key))
        self.assertEqual(200, res.status_code, res.content)
        res = json.loads(res.content)

        self.assertEqual(issue.project.pk, res["project"])
        self.assertEqual(issue.summary, res["summary"])
        self.assertEqual(issue.description, res["description"])
        self.assertEqual(issue.steps_to_reproduce, res["stepsToReproduce"])
        self.assertEqual(issue.priority.short_name, res["priority"])
        self.assertEqual(issue.status, res["status"])
        self.assertEqual(issue.resolution, res["resolution"])
        self.assertSetEqual({c.pk for c in issue.components.all()}, set(res["components"]))
        self.assertSetEqual({v.pk for v in issue.affects_versions.all()}, set(res["affectsVersions"]))
        self.assertSetEqual({v.pk for v in issue.fix_versions.all()}, set(res["fixVersions"]))

    def test_save_issue(self):
        issue = self.generate_issue()

        pl = {
            "project": issue.project.pk,
            "issueType": issue.issue_type.short_name,
            "summary": "New Summary",
            "description": "New Description",
            "stepsToReproduce": "New Steps to Reproduce",
            "priority": random_priority(),
            "status": random_status(),
            "resolution": random_resolution(),
            "assigneeId": self.another_user.pk,
            "components": [self.component_one.pk],
            "affectsVersions": [self.version_two.pk],
            "fixVersions": [self.version_two.pk],
            "milestoneId": None,
        }

        res = self.client.put(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key), json.dumps(pl), content_type="application/json")
        self.assertEqual(200, res.status_code, res.content)
        res = json.loads(res.content)

        self.assertEqual(1, Issue.objects.count())

        issue = Issue.objects.get(pk=issue.pk)
        self.assertAllEqual(pl["project"], issue.project.pk, res["project"])
        self.assertAllEqual(pl["issueType"], issue.issue_type.short_name, res["issueType"])
        self.assertAllEqual(pl["summary"], issue.summary, res["summary"])
        self.assertEqual(pl["description"], issue.description, res["description"])
        self.assertAllEqual(pl["stepsToReproduce"], issue.steps_to_reproduce, res["stepsToReproduce"])
        self.assertAllEqual(pl["priority"], issue.priority.short_name, res["priority"])
        self.assertAllEqual(pl["status"], issue.status, res["status"])
        self.assertAllEqual(pl["resolution"], issue.resolution, res["resolution"])
        self.assertAllEqual(pl["assigneeId"], issue.assignee.pk, res["assignee"]["id"])
        self.assertAllEqual(pl["milestoneId"], None, res["milestone"])
        self.assertAllEqual(self.user.pk, issue.reporter.pk, res["reporter"]["id"])
        self.assertSetEqual(set(pl["components"]), {c.pk for c in issue.components.all()})
        self.assertSetEqual(set(pl["components"]), set(res["components"]))
        self.assertSetEqual(set(pl["affectsVersions"]), {v.pk for v in issue.affects_versions.all()})
        self.assertSetEqual(set(pl["affectsVersions"]), set(res["affectsVersions"]))
        self.assertSetEqual(set(pl["fixVersions"]), {v.pk for v in issue.fix_versions.all()})
        self.assertSetEqual(set(pl["fixVersions"]), set(res["fixVersions"]))

class CommentsApiTests (IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]
    EXISTING_ISSUE_ENDPOINT = "/rest/issues/{0}/"

    def setUp(self):
        self.setUpProject()

    def test_get_comments(self):
        issue = self.generate_issue()
        comment1 = self.generate_comment(issue, author=self.user)
        comment2 = self.generate_comment(issue, author=self.another_user)

        res = self.client.get(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key)+"comments/")
        self.assertEqual(200, res.status_code, res.content)
        res = json.loads(res.content)

        self.assertEqual(2, len(res))
        self.assertEqual(res[0]["text"], comment1.text)
        self.assertEqual(res[0]["author"]["id"], self.user.pk)

        self.assertEqual(res[1]["text"], comment2.text)
        self.assertEqual(res[1]["author"]["id"], self.another_user.pk)

    def test_create_comments(self):
        issue = self.generate_issue()
        comment1 = self.generate_comment(issue, author=self.user)

        pl = {
            "text": random_string(),
        }
        res = self.client.post(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key)+"comments/", json.dumps(pl), content_type="application/json")
        self.assertEqual(200, res.status_code, res.content)
        res = json.loads(res.content)

        issue = Issue.objects.get(pk=issue.pk)
        self.assertEqual(2, issue.comments.count())
        second_comment = issue.comments.get(~Q(pk=comment1.pk))
        self.assertEqual(second_comment.text, pl["text"])
        self.assertEqual(second_comment.author.pk, self.user.pk)
        self.assertIsNotNone(second_comment.created)
        self.assertIsNotNone(second_comment.updated)

    def test_save_comments(self):
        issue = self.generate_issue()
        comment1 = self.generate_comment(issue)
        comment2 = self.generate_comment(issue)

        pl = {
            "id": comment1.pk,
            "text": random_string(),
        }

        res = self.client.put(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key)+"comments/", json.dumps(pl), content_type="application/json")
        self.assertEqual(200, res.status_code, res.content)
        res = json.loads(res.content)

        comment = Comment.objects.get(pk=comment1.pk)
        self.assertEqual(pl["text"], comment.text)

class IssueFilterTests(IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        self.setUpProject()
        self.setUpSecondProject()

    def setUpSecondProject(self):
        project_two = Project(name="Project Two", issue_key="TWO")
        project_two.save()

        c1 = Component(name="Component One", project=project_two)
        c1.save()
        c2 = Component(name="Component Two", project=project_two)
        c2.save()
        v1 = Version(name="Version Two One.0", project=project_two)
        v1.save()
        v2 = Version(name="Version Two Two.0", project=project_two)
        v2.save()

        self.project_two = project_two
        self.project_two_component_one = c1
        self.project_two_component_two = c2
        self.project_two_version_one = v1
        self.project_two_component_two = v2

    def test_filter_by_project(self):
        issue = self.generate_issue()
        issue_noise = self.generate_issue(project=self.project_two, components=[self.project_two_component_one], affects_versions=[], fix_versions=[])

        res = self.client.get("/rest/issues/?projects={0}".format(self.project.issue_key))
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]))
        self.assertEqual(1, res["count"])
        self.assertIsNone(res["next"])
        self.assertIsNone(res["previous"])

        pl = res["results"][0]
        self.assertEqual(issue.issue_key, pl["issueKey"])

    def test_filter_by_status(self):
        issue = self.generate_issue(status="CLOSED", resolution="FIXED")
        issue_noise = self.generate_issue(status="OPEN")

        res = self.client.get("/rest/issues/?statuses=CLOSED")
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]), res)
        self.assertEqual(1, res["count"])
        self.assertIsNone(res["next"])
        self.assertIsNone(res["previous"])

        pl = res["results"][0]
        self.assertEqual(issue.issue_key, pl["issueKey"])

    def test_filter_by_fix_version(self):
        issue = self.generate_issue(fix_versions=[self.version_one])
        issue_noise = self.generate_issue(fix_versions=[self.version_two])

        res = self.client.get("/rest/issues/?fix_versions={0}".format(self.version_one.pk))
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]))
        pl = res["results"][0]
        self.assertEqual(issue.issue_key, pl["issueKey"])

    def test_filter_by_affects_version(self):
        issue = self.generate_issue(affects_versions=[self.version_one])
        issue_noise = self.generate_issue(affects_versions=[self.version_two])

        res = self.client.get("/rest/issues/?affects_versions={0}".format(self.version_one.pk))
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]))
        pl = res["results"][0]
        self.assertEqual(issue.issue_key, pl["issueKey"])

    def test_filter_by_assignee(self):
        issue = self.generate_issue(assignee=self.user)
        issue_noise = self.generate_issue(assignee=self.another_user)

        res = self.client.get("/rest/issues/?assignees={0}".format(self.user.pk))
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]))
        pl = res["results"][0]
        self.assertEqual(issue.issue_key, pl["issueKey"])

    def test_order_by_priority(self):
        issue_min = self.generate_issue(priority="MIN")
        issue_blk = self.generate_issue(priority="BLK")
        issue_maj = self.generate_issue(priority="MAJ")

        res = self.client.get("/rest/issues/?order_by=priority")
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(3, len(res["results"]))
        self.assertListEqual([issue_blk.pk, issue_maj.pk, issue_min.pk], [i["id"] for i in res["results"]])

    def test_filter_by_term_issue_key(self):
        issue1 = self.generate_issue()
        # noise
        issue2 = self.generate_issue()
        issue3 = self.generate_issue()

        res = self.client.get("/rest/issues/?terms={0}".format(issue1.issue_key))
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(1, len(res["results"]))
        self.assertEqual(issue1.issue_key, res["results"][0]["issueKey"])

    def test_filter_by_term(self):
        issue1 = self.generate_issue()
        issue2 = self.generate_issue(summary="{0} summary {1}".format(random_string(15), random_string(15)))
        issue3 = self.generate_issue(description="{0} summary {1}".format(random_string(), random_string()))

        res = self.client.get("/rest/issues/?terms=summary")
        self.assertEqual(200, res.status_code)
        res = json.loads(res.content)

        self.assertEqual(2, len(res["results"]))
        self.assertSetEqual({issue2.issue_key, issue3.issue_key}, set(r["issueKey"] for r in res["results"]))









