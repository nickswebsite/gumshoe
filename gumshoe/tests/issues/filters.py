import json

from django.test import TestCase as TestCaseBase

from gumshoe.models import Project, Component, Version
from gumshoe.tests.utils import IssueTestCaseBase, random_string


class IssueFilterTests(IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]

    def setUp(self):
        self.setUpProject()
        self.setUpSecondProject()

    def setUpSecondProject(self):
        project_two = Project(name="Project Two", issue_key="TWO")
        project_two.save()

        component_one = Component(name="Component One", project=project_two)
        component_one.save()
        component_two = Component(name="Component Two", project=project_two)
        component_two.save()

        version_one = Version(name="Version Two One.0", project=project_two)
        version_one.save()
        version_two = Version(name="Version Two Two.0", project=project_two)
        version_two.save()

        self.project_two = project_two
        self.project_two_component_one = component_one
        self.project_two_component_two = component_two
        self.project_two_version_one = version_one
        self.project_two_component_two = version_two

    def test_filter_by_project(self):
        issue = self.generate_issue()

        # Noise
        _ = self.generate_issue(project=self.project_two, components=[self.project_two_component_one], affects_versions=[], fix_versions=[])

        response = self.client.get("/rest/issues/?projects={0}".format(self.project.issue_key))
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]))
        self.assertEqual(1, pl["count"])
        self.assertIsNone(pl["next"])
        self.assertIsNone(pl["previous"])

        result = pl["results"][0]
        self.assertEqual(issue.issue_key, result["issueKey"])

    def test_filter_by_status(self):
        issue = self.generate_issue(status="CLOSED", resolution="FIXED")

        # Noise
        _ = self.generate_issue(status="OPEN")

        response = self.client.get("/rest/issues/?statuses=CLOSED")
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]), pl)
        self.assertEqual(1, pl["count"])
        self.assertIsNone(pl["next"])
        self.assertIsNone(pl["previous"])

        result = pl["results"][0]
        self.assertEqual(issue.issue_key, result["issueKey"])

    def test_filter_by_fix_version(self):
        issue = self.generate_issue(fix_versions=[self.version_one])

        # noise
        _ = self.generate_issue(fix_versions=[self.version_two])

        response = self.client.get("/rest/issues/?fix_versions={0}".format(self.version_one.pk))
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]))
        result = pl["results"][0]
        self.assertEqual(issue.issue_key, result["issueKey"])

    def test_filter_by_affects_version(self):
        issue = self.generate_issue(affects_versions=[self.version_one])

        # noise
        _ = self.generate_issue(affects_versions=[self.version_two])

        response = self.client.get("/rest/issues/?affects_versions={0}".format(self.version_one.pk))
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]))
        result = pl["results"][0]
        self.assertEqual(issue.issue_key, result["issueKey"])

    def test_filter_by_assignee(self):
        issue = self.generate_issue(assignee=self.user)

        # noise
        _ = self.generate_issue(assignee=self.another_user)

        response = self.client.get("/rest/issues/?assignees={0}".format(self.user.pk))
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]))
        result = pl["results"][0]
        self.assertEqual(issue.issue_key, result["issueKey"])

    def test_order_by_priority(self):
        issue_min = self.generate_issue(priority="MIN")
        issue_blk = self.generate_issue(priority="BLK")
        issue_maj = self.generate_issue(priority="MAJ")

        response = self.client.get("/rest/issues/?order_by=priority")
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(3, len(pl["results"]))
        self.assertListEqual([issue_blk.pk, issue_maj.pk, issue_min.pk], [i["id"] for i in pl["results"]])

    def test_filter_by_term_issue_key(self):
        issue = self.generate_issue()

        # noise
        _ = self.generate_issue()
        _ = self.generate_issue()

        response = self.client.get("/rest/issues/?terms={0}".format(issue.issue_key))
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(1, len(pl["results"]))
        self.assertEqual(issue.issue_key, pl["results"][0]["issueKey"])

    def test_filter_by_term(self):
        issue_one = self.generate_issue()
        issue_two = self.generate_issue(summary="{0} summary {1}".format(random_string(15), random_string(15)))
        issue_three = self.generate_issue(description="{0} summary {1}".format(random_string(), random_string()))

        response = self.client.get("/rest/issues/?terms=summary")
        self.assertEqual(200, response.status_code)

        pl = json.loads(response.content)

        self.assertEqual(2, len(pl["results"]))
        self.assertSetEqual({issue_two.issue_key, issue_three.issue_key}, set(r["issueKey"] for r in pl["results"]))