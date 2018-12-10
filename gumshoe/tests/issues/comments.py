import json

from django.db.models import Q
from django.test import TestCase as TestCaseBase

from gumshoe.models import Issue, Comment
from gumshoe.tests.utils import IssueTestCaseBase, random_string


class CommentsApiTests (IssueTestCaseBase, TestCaseBase):
    fixtures = ["initial_data.json"]
    COMMENTS_URI_TEMPLATE = "/rest/issues/{issue_key}/comments/"

    def setUp(self):
        self.setUpProject()

    def test_get_comments(self):
        issue = self.generate_issue()
        comment_one = self.generate_comment(issue, author=self.user)
        comment_two = self.generate_comment(issue, author=self.another_user)

        response = self.client.get(self.COMMENTS_URI_TEMPLATE.format(issue_key=issue.issue_key))
        self.assertEqual(200, response.status_code, response.content)

        response_pl = json.loads(response.content)

        self.assertEqual(2, len(response_pl["results"]))
        self.assertEqual(response_pl["results"][0]["text"], comment_one.text)
        self.assertEqual(response_pl["results"][0]["author"]["id"], self.user.pk)

        self.assertEqual(response_pl["results"][1]["text"], comment_two.text)
        self.assertEqual(response_pl["results"][1]["author"]["id"], self.another_user.pk)

    def test_create_comments(self):
        issue = self.generate_issue()
        comment = self.generate_comment(issue, author=self.user)

        request_pl = {
            "text": random_string(),
        }
        response = self.client.post(self.COMMENTS_URI_TEMPLATE.format(issue_key=issue.issue_key), json.dumps(request_pl), content_type="application/json")
        self.assertEqual(201, response.status_code, response.content)

        response_pl = json.loads(response.content)

        issue_result = Issue.objects.get(pk=issue.pk)
        self.assertEqual(2, issue_result.comments.count())

        second_comment = issue_result.comments.get(~Q(pk=comment.pk))
        self.assertEqual(second_comment.text, request_pl["text"])
        self.assertEqual(second_comment.author.pk, self.user.pk)
        self.assertIsNotNone(second_comment.created)
        self.assertIsNotNone(second_comment.updated)

    def test_create_comments_for_non_existing_issue(self):
        request_pl = {
            "text": random_string()
        }

        response = self.client.post(self.COMMENTS_URI_TEMPLATE.format(issue_key="SOME_RANDOM_KEY"), json.dumps(request_pl), content_type="application/json")

        self.assertEqual(response.status_code, 404)

    def test_get_comments_for_non_existing_issue(self):
        response = self.client.get(self.COMMENTS_URI_TEMPLATE.format(issue_key="SOME_RANDOM_KEY"), content_type="application/json")

        self.assertEqual(response.status_code, 404)

    def test_save_comments(self):
        issue = self.generate_issue()

        comment_one = self.generate_comment(issue)

        # Noise
        _ = self.generate_comment(issue)

        request_pl = {
            "text": random_string(),
        }
        response = self.client.put(f"/rest/comments/{comment_one.pk}", json.dumps(request_pl), content_type="application/json")

        self.assertEqual(200, response.status_code, response.content)

        response_pl = json.loads(response.content)

        comment = Comment.objects.get(pk=comment_one.pk)
        self.assertEqual(request_pl["text"], comment.text)
