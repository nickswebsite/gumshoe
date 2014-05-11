from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from gumshoe.urls import standalone_urlpatterns

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(standalone_urlpatterns, app_name="gumshoe")),
)
