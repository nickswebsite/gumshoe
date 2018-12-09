from django.contrib import admin
from django.urls import path

from gumshoe.urls import standalone_urlpatterns

admin.autodiscover()

urlpatterns = [path("admin/", admin.site.urls)] + standalone_urlpatterns
