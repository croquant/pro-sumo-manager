"""
URL configuration for Pro Sumo Manager django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from game.views import dashboard, index, setup_draft_pool, setup_heya_name

urlpatterns = [
    path("", index, name="index"),
    path("dashboard/", dashboard, name="dashboard"),
    path("setup/heya-name/", setup_heya_name, name="setup_heya_name"),
    path("setup/draft/", setup_draft_pool, name="setup_draft_pool"),
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
