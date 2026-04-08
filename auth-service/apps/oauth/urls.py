from django.urls import path
from apps.oauth.views import (
    JiraCallbackView,
    JiraLoginView,
    LogoutView,
    RefreshTokenView,
)

urlpatterns = [
    path("oauth/jira/login/", JiraLoginView.as_view(), name="jira-login"),
    path("oauth/jira/callback/", JiraCallbackView.as_view(), name="jira-callback"),
    path("oauth/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("oauth/logout/", LogoutView.as_view(), name="logout"),
]
