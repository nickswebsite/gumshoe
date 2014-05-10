import re
import os

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.db import connections
from django.contrib.auth.models import User
from django.db import models
from gumshoe.models import Project, Version, Component, Priority, IssueType, Issue, Comment

TEMPORARY_TABLE_NAME = "bugzillaimport"
class BugzillaIssueMap(models.Model):
    bugzilla_id = models.IntegerField(primary_key=True)
    issue = models.ForeignKey(Issue)

    class Meta:
        managed = False
        db_table = TEMPORARY_TABLE_NAME

camel_case_split_pattern = r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))'
def project_name_to_keys(name):
    """
    Returns a list of possible issue keys based on the name.  The first key
    in the list is the most recommended.

    :param name: The human readable name for the project.

    :return: Returns a list of suggested issue keys.
    """
    # Covers most common multiword cases like Project Name, Project Name
    if " " in name.strip():
        parts = name.strip().split(" ")
    # Covers cases like Project_Name
    elif "_" in name:
        parts = name.strip().split("_")
    # Covers cases like ProjectName or projectName
    else:
        ss = re.sub(camel_case_split_pattern, r' \1', name.strip())
        parts = ss.split()

    project_words = [part.strip().upper() for part in parts if part.strip().upper() not in ("", "THE", "A")]
    suggestions = [project_words[0]]
    if len(project_words) > 1:
        # For multi word project names the next suggestion is the acronym
        # e.g. Project Name, after PROJECT, the next suggestion will be PN
        suggestions.append("".join([w[0] for w in project_words]))
        # The next suggestion will be PROJECTNAME
        suggestions.append("".join(project_words))
    suggestions += project_words[1:]

    return suggestions

def email_to_username(email):
    username = email.replace("@", "-")

    return [username]

def import_projects(project_list, key_map=None):
    key_map = key_map or {}
    issue_keys_taken = {p.issue_key for p in Project.objects.all()}
    for key in key_map:
        if key in issue_keys_taken:
            raise ValueError("Issue key specified is already taken.")

    for project in project_list:
        issue_key = key_map.get(project.name)
        if not issue_key:
            possible_issue_keys = iter(project_name_to_keys(project.name))
            issue_key = possible_issue_keys.next()
            while issue_key in issue_keys_taken:
                issue_key = possible_issue_keys.next()
        project.issue_key = issue_key
        issue_keys_taken.add(issue_key)
        project.save()

import sys

def default_log_dot_fn():
    sys.stdout.write(".")

def rowdict(row, cur):
    if hasattr(cur, "description"):
        return dict(zip([d[0] for d in cur.description], row))
    return dict(zip(cur, row))

def rowdict_cursor(cur):
    fields = [d[0] for d in cur.description]
    for row in cur:
        yield rowdict(row, fields)

class DotLogger(object):
    def __init__(self, cnt=1, fn=default_log_dot_fn):
        self.cnt = cnt
        self.fn = fn
        self.cur = 0

    def __call__(self):
        if self.cur >= self.cnt:
            self.fn()
            self.cur = 0
        self.cur += 1

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--database", "-D", dest="database", default='bugzilla',
            help="Database connection to use."
        ),

        make_option(
            "--user-map", "-U", dest="user_map", action="append",
            help="A mapping of a user's email address to their username of the form 'some-email@email.com=some-username"
        ),

        make_option(
            "--project-key-map", "-K", dest="project_key_map", action="append",
            help="Project key map in the form of 'Project Name=PROJECTKEY'."
        ),
    )
    help = 'Imports bugs from a bugzilla database.'

    default_status_map = {
        "CONFIRMED": "OPEN",
        "OPEN": "OPEN",
        "IN_PROGRESS": "OPEN",
        "RESOLVED": "RESOLVED",
        "VERIFIED": "RESOLVED",
        "CLOSED": "CLOSED",
    }

    default_resolution_map = {
        None: "UNRESOLVED",
        "": "UNRESOLVED",
        "DUPLICATE": "INVALID",
        "FIXED": "FIXED",
        "INVALID": "INVALID",
        "WONTFIX": "WONT_FIX",
        "WORKSFORME": "INVALID",
    }

    default_priority_map = {
        "blocker": "BLK",
        "critical": "BLK",
        "major": "MAJ",
        "normal": "MAJ",
        "minor": "MIN",
        "enhancement": "MIN",
    }

    default_issue_type_map = {
        "Feature Request": "FRQ",
        "Bug": "BUG",
        "Task": "TASK",
    }

    default_issue_type = "Bug"

    default_issue_type_field = "cf_issue_type"

    def create_temporary_tables(self):
        conn = connections["default"]
        cur = conn.cursor()
        q = """
            CREATE TEMPORARY TABLE {0} (
                bugzilla_id INTEGER,
                issue_id INTEGER
            )
        """.format(TEMPORARY_TABLE_NAME)
        cur.execute(q)

    def split_key_value_pairs(self, args):
        return dict(tuple(arg.split("=") for arg in args))

    def handle(self, *args, **options):
        def log(msg):
            sys.stdout.write(msg)
            sys.stdout.flush()

        print(args, options)

        print("Setting up project key maps.")
        project_key_map_args = options.get("project_key_map") or []
        project_key_map = self.split_key_value_pairs(project_key_map_args)
        print(project_key_map)

        print("Initializing username mappings")
        user_name_map = self.split_key_value_pairs(options.get("user_map") or [])
        user_map = {}

        print("Initializing priority mappings.")
        priority_name_map = self.default_priority_map
        priority_map = {k: Priority.objects.get(short_name=v) for k, v in priority_name_map.items()}

        print("Initializing resolution mappings.")
        resolution_map = self.default_resolution_map
        status_map = self.default_status_map

        print("Initializing issue type mappings.")
        issue_type_name_map = self.default_issue_type_map
        issue_type_map = {k: IssueType.objects.get(short_name=v) for k, v in issue_type_name_map.items()}
        default_issue_type = issue_type_map[self.default_issue_type]

        log_dot = DotLogger()

        cur = None
        try:
            self.create_temporary_tables()

            print("Acquiring connection.")
            conn = connections[options.get("database")]
            cur = conn.cursor()


            print("Importing users.")
            cur.execute("SELECT userid, login_name FROM profiles")
            for row in cur:
                username = user_name_map.get(row[1]) or row[1]

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    try:
                        user = User.objects.get(email=username)
                    except User.DoesNotExist:
                        user = User(username=username, email=row[1], password=username)
                        user.save()

                user_map[row[0]] = user.pk

            print("Importing products as projects.")
            cur.execute("SELECT id, name, description FROM products")
            all_projects = {row[0]: Project(name=row[1], description=row[2]) for row in cur}

            import_projects(all_projects.values(), project_key_map)

            print("Importing versions.")
            cur.execute("SELECT id, value, product_id from versions")
            for row in cur:
                project = all_projects.get(row[2])
                version = Version(name=row[1], description="Autoimport from bugzilla.", project=project)
                version.save()

            print("Importing components.")
            cur.execute("SELECT id, name, description, product_id from components")
            for row in cur:
                project = all_projects.get(row[-1])
                component = Component(name=row[1], description=row[2], project=project)
                component.save()

            print("Importing issues.")
            print("starting query")
            issue_type_field_clause = ", cf_issue_type AS issue_type"
            cur.execute("""
                SELECT bug.bug_id AS id,
                       assignee.login_name AS assignee,
                       bug.product_id AS product_id,
                       bug.bug_severity AS priority,
                       bug.bug_status AS status,
                       bug.creation_ts AS creation_time,
                       bug.delta_ts AS delta_time,
                       bug.short_desc AS summary,
                       reporter.login_name AS reporter,
                       bug.version AS version_name,
                       c.name AS component_name,
                       bug.lastdiffed AS last_changed,
                       bug.resolution AS resolution
                       {0}
                FROM bugs bug
                JOIN profiles assignee ON bug.assigned_to = assignee.userid
                JOIN profiles reporter ON bug.reporter = reporter.userid
                LEFT JOIN components c ON bug.component_id = c.id
            """.format(issue_type_field_clause))
            print("query done")

            for row in rowdict_cursor(cur):
                assignee = User.objects.get(email=row["assignee"])
                project = all_projects[row["product_id"]]
                priority = priority_map[row["priority"]]
                status = status_map[row["status"]]
                creation_time = row["creation_time"]
                delta_time = row["delta_time"]
                summary = row["summary"]
                reporter = User.objects.get(email=row["reporter"])
                version = project.version_set.get(name=row["version_name"])
                component = project.component_set.get(name=row["component_name"])
                last_changed = row["last_changed"]
                resolution = resolution_map[row["resolution"]]
                issue_type = issue_type_map.get(row["issue_type"], default_issue_type)

                issue = Issue()
                issue.project = project
                issue.issue_type = issue_type
                issue.assignee = assignee
                issue.reporter = reporter
                issue.priority = priority
                issue.summary = summary
                issue.status = status
                issue.resolution = resolution
                issue.reported = creation_time
                issue.last_updated = last_changed
                issue.save(update_timestamps=False)

                issue.affects_versions = [version]
                issue.fix_versions = [version]
                issue.components = [component]

                bugzilla_map = BugzillaIssueMap()
                bugzilla_map.issue = issue
                bugzilla_map.bugzilla_id = row["id"]
                bugzilla_map.save()

                log_dot()

            print("")
            print("Importing comments.")
            cur.execute("""
                SELECT d.bug_id AS bug,
                       p.login_name AS user_email,
                       d.bug_when AS timestamp,
                       d.thetext AS description
                FROM longdescs d
                JOIN profiles p ON d.who = p.userid
                ORDER BY bug
            """)
            for row in rowdict_cursor(cur):
                bugzilla_map = BugzillaIssueMap.objects.get(bugzilla_id=row["bug"])
                author = User.objects.get(email=row["user_email"])
                timestamp = row["timestamp"]
                text = row["description"]

                if text:
                    if timestamp == bugzilla_map.issue.reported:
                        bugzilla_map.issue.description += text
                        bugzilla_map.issue.save(update_timestamps=False)
                    else:
                        comment = Comment()
                        comment.content = bugzilla_map.issue
                        comment.text = text
                        comment.author = author
                        comment.created = timestamp
                        comment.updated = timestamp
                        comment.save(update_timestamps=False)

                log_dot()

        finally:
            if cur is not None:
                cur.close()


