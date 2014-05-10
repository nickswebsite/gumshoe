from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import gumshoe.views


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_tracker.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', 'gumshoe.views.login', name='login'),
    url(r'^logout/', 'gumshoe.views.logout', name='logout'),
    url(r'^forms/add_issue', 'gumshoe.views.issue_form', name='add_issue_form'),
    url(r'^issues/(?P<issue_key>[A-Z]+-\d+)$', 'gumshoe.views.issue_form', name='edit_issue_form'),
    url(r'^$', 'gumshoe.views.issue_list_view', name='issues_list_form'),

    url(r'^test/', 'gumshoe.views.test_view', name='test_view'),
    url(r'^tests', 'gumshoe.views.tests_view', name='issues_test'),

    url(r'rest/', include(gumshoe.views.router.urls)),
    url(r'^rest/settings/$', 'gumshoe.views.settings_view', name='settings'),
    url(r'^rest/components/(?P<pk>[0-9]+)', gumshoe.views.ComponentDetailView.as_view(), name="components_detail"),
    url(r'^rest/versions/(?P<pk>[0-9]+)', gumshoe.views.VersionDetailView.as_view(), name='versions_detail'),
)

