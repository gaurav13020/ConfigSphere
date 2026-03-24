from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models.deletion import ProtectedError

from .models import SchemaDefinition
from .serializers import SchemaDefinitionCreateSerializer, SchemaDefinitionSerializer, SchemaDefinitionUpdateSerializer
from .services import SchemaService
from common.exceptions import NotFoundError


class SchemaDefinitionListCreateView(APIView):
    def get(self, request):
        schemas = SchemaDefinition.objects.all()
        serializer = SchemaDefinitionSerializer(schemas, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SchemaDefinitionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schema = SchemaService.create(
            name=serializer.validated_data["name"],
            schema_json=serializer.validated_data["schema_json"],
            description=serializer.validated_data.get("description", ""),
        )

        return Response(SchemaDefinitionSerializer(schema).data, status=status.HTTP_201_CREATED)


class SchemaDefinitionDetailView(APIView):
    def get(self, request, pk):
        try:
            schema = SchemaDefinition.objects.get(pk=pk)
        except SchemaDefinition.DoesNotExist:
            raise NotFoundError(f"Schema with id={pk} does not exist.")
        return Response(SchemaDefinitionSerializer(schema).data)

    def put(self, request, pk):
        try:
            schema = SchemaDefinition.objects.get(pk=pk)
        except SchemaDefinition.DoesNotExist:
            raise NotFoundError(f"Schema with id={pk} does not exist.")

        serializer = SchemaDefinitionUpdateSerializer(data=request.data, schema_id=pk)
        serializer.is_valid(raise_exception=True)

        schema.name = serializer.validated_data["name"]
        schema.description = serializer.validated_data.get("description", "")
        schema.schema_json = serializer.validated_data["schema_json"]
        schema.save()

        return Response(SchemaDefinitionSerializer(schema).data)

    def delete(self, request, pk):
        try:
            schema = SchemaDefinition.objects.get(pk=pk)
        except SchemaDefinition.DoesNotExist:
            raise NotFoundError(f"Schema with id={pk} does not exist.")

        try:
            schema.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            return Response(
                {
                    "error": "Cannot delete this schema because it is currently used by Config Items. Please remove or reassign the Config Items first.",
                    "details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "error": "Failed to delete schema",
                    "details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
