from django.conf import settings
from django.urls import re_path, include

import gumshoe.views


rest_urlpatterns = [
    re_path(r'^', include(gumshoe.views.router.urls)),
    re_path(r'^pages/$', gumshoe.views.pages_view, name='pages'),
    re_path(r'^settings/$', gumshoe.views.settings_view, name='settings'),
    re_path(r'^components/(?P<pk>[0-9]+)$', gumshoe.views.ComponentDetailView.as_view(), name="components_detail"),
    re_path(r'^versions/(?P<pk>[0-9]+)$', gumshoe.views.VersionDetailView.as_view(), name='versions_detail'),
    re_path(r'^issues/(?P<issue_key>[-A-Za-z0-9_]+)/comments/$', gumshoe.views.CommentCollectionView.as_view(), name="comment_collection"),
    re_path(r'^comments/(?P<pk>[0-9]+)$', gumshoe.views.CommentRetrieveUpdateDestroyView.as_view(), name="comment-detail"),
]

page_urlpatterns = [
    re_path(r'^$', gumshoe.views.index, name='index'),
    re_path(r'^issues/_add$', gumshoe.views.issue_form, name='issues_add_form'),
    re_path(r'^issues/(?P<issue_key>[A-Z]+-\d+)$', gumshoe.views.issue_form, name='issue_edit_form'),
    re_path(r'^issues/$', gumshoe.views.issue_list_view, name='issues_list_form'),
]

test_urlpatterns = [
    # re_path(r'^$', 'gumshoe.views.tests_view', name='issues_test'),
]

standalone_urlpatterns = [
    re_path(r'^login/', gumshoe.views.login, name='login'),
    re_path(r'^logout/', gumshoe.views.logout, name='logout'),
    re_path(r'^rest/', include(rest_urlpatterns)),
    re_path(r'^', include(page_urlpatterns)),
]

if getattr(settings, 'DEBUG', False):
    standalone_urlpatterns += [re_path(r'^tests/', include(test_urlpatterns))]
