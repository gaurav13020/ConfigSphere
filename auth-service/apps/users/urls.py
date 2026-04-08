from django.urls import path
from apps.users.views import (
    MeView,
    RoleMappingDetailView,
    RoleMappingListCreateView,
    UserListView,
    UserRoleOverrideView,
)

urlpatterns = [
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/role/", UserRoleOverrideView.as_view(), name="user-role-override"),
    path("role-mappings/", RoleMappingListCreateView.as_view(), name="role-mapping-list"),
    path("role-mappings/<int:pk>/", RoleMappingDetailView.as_view(), name="role-mapping-detail"),
]
