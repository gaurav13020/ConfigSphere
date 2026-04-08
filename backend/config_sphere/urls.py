from django.contrib import admin
from django.urls import include, path

API_PREFIX = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(API_PREFIX, include("apps.schemas.urls")),
    path(API_PREFIX, include("apps.configs.urls")),
    path(API_PREFIX, include("apps.audits.urls")),
    path(API_PREFIX, include("apps.approvals.urls")),
]
