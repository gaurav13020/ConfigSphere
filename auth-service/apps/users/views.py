from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import JiraRoleMapping, JiraUser
from apps.users.serializers import (
    JiraRoleMappingSerializer,
    JiraUserSerializer,
    RoleOverrideSerializer,
)
from common.constants import ConfigSphereRole
from common.permissions import IsAdmin, IsViewer


class MeView(APIView):
    """
    GET /api/v1/users/me/
    Returns the current authenticated user's profile and role.
    Any authenticated user can call this.
    """

    permission_classes = [IsViewer]

    def get(self, request):
        try:
            user = JiraUser.objects.get(
                jira_account_id=request.user.jira_account_id
            )
        except JiraUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(JiraUserSerializer(user).data)


class UserListView(ListAPIView):
    """
    GET /api/v1/users/
    Lists all JiraUsers. Admin only.
    """

    permission_classes = [IsAdmin]
    serializer_class = JiraUserSerializer
    queryset = JiraUser.objects.all()


class UserRoleOverrideView(APIView):
    """
    PATCH /api/v1/users/{id}/role/
    Allows an Admin to manually assign a role to a user, bypassing Jira
    group/role derivation (sets role_override=True).

    PATCH with role_override=False re-enables automatic role derivation.
    """

    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            user = JiraUser.objects.get(pk=pk)
        except JiraUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = RoleOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.configsphere_role = serializer.validated_data["configsphere_role"]
        user.role_override = serializer.validated_data["role_override"]
        user.save(update_fields=["configsphere_role", "role_override", "updated_at"])

        return Response(JiraUserSerializer(user).data)


class RoleMappingListCreateView(APIView):
    """
    GET  /api/v1/role-mappings/   — list all Jira→ConfigSphere role mappings
    POST /api/v1/role-mappings/   — create a new mapping
    Both require Admin.
    """

    permission_classes = [IsAdmin]

    def get(self, request):
        mappings = JiraRoleMapping.objects.all()
        return Response(JiraRoleMappingSerializer(mappings, many=True).data)

    def post(self, request):
        serializer = JiraRoleMappingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save()
        return Response(
            JiraRoleMappingSerializer(mapping).data,
            status=status.HTTP_201_CREATED,
        )


class RoleMappingDetailView(APIView):
    """
    PUT    /api/v1/role-mappings/{id}/  — update a mapping
    DELETE /api/v1/role-mappings/{id}/  — remove a mapping
    Both require Admin.
    """

    permission_classes = [IsAdmin]

    def _get_object(self, pk):
        try:
            return JiraRoleMapping.objects.get(pk=pk)
        except JiraRoleMapping.DoesNotExist:
            return None

    def put(self, request, pk):
        mapping = self._get_object(pk)
        if not mapping:
            return Response(
                {"error": "Role mapping not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = JiraRoleMappingSerializer(mapping, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        mapping = self._get_object(pk)
        if not mapping:
            return Response(
                {"error": "Role mapping not found."}, status=status.HTTP_404_NOT_FOUND
            )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
