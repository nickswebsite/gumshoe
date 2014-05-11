from django.conf.urls import patterns, include, url
from django.conf import settings

import gumshoe.views

rest_urlpatterns = patterns('',
    url(r'^', include(gumshoe.views.router.urls)),
    url(r'^pages/$', 'gumshoe.views.pages_view', name='pages'),
    url(r'^settings/$', 'gumshoe.views.settings_view', name='settings'),
    url(r'^components/(?P<pk>[0-9]+)$', gumshoe.views.ComponentDetailView.as_view(), name="components_detail"),
    url(r'^versions/(?P<pk>[0-9]+)$', gumshoe.views.VersionDetailView.as_view(), name='versions_detail'),
)

page_urlpatterns = patterns('',
    url(r'^$', 'gumshoe.views.index', name='index'),
    url(r'^issues/_add$', 'gumshoe.views.issue_form', name='issues_add_form'),
    url(r'^issues/(?P<issue_key>[A-Z]+-\d+)$', 'gumshoe.views.issue_form', name='issue_edit_form'),
    url(r'^issues/$', 'gumshoe.views.issue_list_view', name='issues_list_form'),
)

test_urlpatterns = patterns('',
    url(r'^$', 'gumshoe.views.tests_view', name='issues_test'),
)

standalone_urlpatterns = patterns('',
    url(r'^login/', 'gumshoe.views.login', name='login'),
    url(r'^logout/', 'gumshoe.views.logout', name='logout'),
    url(r'^rest/', include(rest_urlpatterns)),
    url(r'^', include(page_urlpatterns)),
)

#if getattr(settings, 'DEBUG', False):
#    standalone_urlpatterns += url(r'^tests/', include(test_urlpatterns))
