from django.urls import path, include

API_PREFIX = "api/v1/"

urlpatterns = [
    path(API_PREFIX, include("apps.oauth.urls")),
    path(API_PREFIX, include("apps.users.urls")),
]
