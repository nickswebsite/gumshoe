import json

from django.test import TestCase as TestCaseBase

from gumshoe.models import Issue
from gumshoe.tests.utils import IssueTestCaseBase, random_issue_type, random_string, random_priority, random_status, \
    random_resolution


class IssuesApiTests (IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]
    NEW_ISSUES_ENDPOINT = "/rest/issues/"
    EXISTING_ISSUE_ENDPOINT = "/rest/issues/{0}/"

    def setUp(self):
        self.setUpProject()

    def test_new_issue(self):
        self.project.versions = [self.version_one, self.version_two]
        request_pl = {
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

        if request_pl["status"] == "OPEN":
            request_pl["resolution"] = Issue.RESOLUTION_CHOICES[0][0]

        response = self.client.post(self.NEW_ISSUES_ENDPOINT, json.dumps(request_pl), content_type="application/json")
        self.assertEqual(201, response.status_code, response.content)

        response_pl = json.loads(response.content)

        self.assertEqual(1, Issue.objects.count())
        issue = Issue.objects.get(pk=1)

        self.assertAllEqual(self.project.pk, response_pl["project"], issue.project.pk)
        self.assertAllEqual(self.project.issue_key + "-1", response_pl["issueKey"], issue.issue_key)
        self.assertAllEqual(request_pl["issueType"], response_pl["issueType"], issue.issue_type.short_name)
        self.assertAllEqual(request_pl["summary"], response_pl["summary"], issue.summary)
        self.assertAllEqual(request_pl["description"], response_pl["description"], issue.description)
        self.assertAllEqual(request_pl["stepsToReproduce"], response_pl["stepsToReproduce"], issue.steps_to_reproduce)
        self.assertAllEqual(request_pl["priority"], response_pl["priority"], issue.priority.short_name)
        self.assertAllEqual(request_pl["status"], response_pl["status"], issue.status)
        self.assertAllEqual(request_pl["resolution"], response_pl["resolution"], issue.resolution)
        self.assertAllEqual(self.user.pk, response_pl["reporter"]["id"], issue.reporter.pk)
        self.assertAllEqual(self.user.pk, response_pl["assignee"]["id"], issue.assignee.pk)
        self.assertSetEqual(set(request_pl["components"]), {c.pk for c in issue.components.all()})
        self.assertSetEqual(set(request_pl["components"]), set(response_pl["components"]))
        self.assertSetEqual(set(request_pl["affectsVersions"]), {v.pk for v in issue.affects_versions.all()})
        self.assertSetEqual(set(request_pl["affectsVersions"]), set(response_pl["affectsVersions"]))
        self.assertSetEqual(set(request_pl["fixVersions"]), {v.pk for v in issue.fix_versions.all()})
        self.assertSetEqual(set(request_pl["fixVersions"]), set(response_pl["fixVersions"]))
        self.assertAllEqual(self.milestone.pk, response_pl["milestone"]["id"], issue.milestone.pk)

    def test_get_issue(self):
        issue = self.generate_issue()

        response = self.client.get(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key))
        self.assertEqual(200, response.status_code, response.content)

        response_pl = json.loads(response.content)

        self.assertEqual(issue.project.pk, response_pl["project"])
        self.assertEqual(issue.summary, response_pl["summary"])
        self.assertEqual(issue.description, response_pl["description"])
        self.assertEqual(issue.steps_to_reproduce, response_pl["stepsToReproduce"])
        self.assertEqual(issue.priority.short_name, response_pl["priority"])
        self.assertEqual(issue.status, response_pl["status"])
        self.assertEqual(issue.resolution, response_pl["resolution"])
        self.assertSetEqual({c.pk for c in issue.components.all()}, set(response_pl["components"]))
        self.assertSetEqual({v.pk for v in issue.affects_versions.all()}, set(response_pl["affectsVersions"]))
        self.assertSetEqual({v.pk for v in issue.fix_versions.all()}, set(response_pl["fixVersions"]))

    def test_save_issue(self):
        issue = self.generate_issue()

        request_pl = {
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

        response = self.client.put(self.EXISTING_ISSUE_ENDPOINT.format(issue.issue_key), json.dumps(request_pl), content_type="application/json")
        self.assertEqual(200, response.status_code, response.content)

        response_pl = json.loads(response.content)

        self.assertEqual(1, Issue.objects.count())

        issue = Issue.objects.get(pk=issue.pk)
        self.assertAllEqual(request_pl["project"], issue.project.pk, response_pl["project"])
        self.assertAllEqual(request_pl["issueType"], issue.issue_type.short_name, response_pl["issueType"])
        self.assertAllEqual(request_pl["summary"], issue.summary, response_pl["summary"])
        self.assertEqual(request_pl["description"], issue.description, response_pl["description"])
        self.assertAllEqual(request_pl["stepsToReproduce"], issue.steps_to_reproduce, response_pl["stepsToReproduce"])
        self.assertAllEqual(request_pl["priority"], issue.priority.short_name, response_pl["priority"])
        self.assertAllEqual(request_pl["status"], issue.status, response_pl["status"])
        self.assertAllEqual(request_pl["resolution"], issue.resolution, response_pl["resolution"])
        self.assertAllEqual(request_pl["assigneeId"], issue.assignee.pk, response_pl["assignee"]["id"])
        self.assertAllEqual(request_pl["milestoneId"], None, response_pl["milestone"])
        self.assertAllEqual(self.user.pk, issue.reporter.pk, response_pl["reporter"]["id"])
        self.assertSetEqual(set(request_pl["components"]), {c.pk for c in issue.components.all()})
        self.assertSetEqual(set(request_pl["components"]), set(response_pl["components"]))
        self.assertSetEqual(set(request_pl["affectsVersions"]), {v.pk for v in issue.affects_versions.all()})
        self.assertSetEqual(set(request_pl["affectsVersions"]), set(response_pl["affectsVersions"]))
        self.assertSetEqual(set(request_pl["fixVersions"]), {v.pk for v in issue.fix_versions.all()})
        self.assertSetEqual(set(request_pl["fixVersions"]), set(response_pl["fixVersions"]))