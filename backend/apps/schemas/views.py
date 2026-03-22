from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from .models import SchemaDefinition
from .serializers import SchemaDefinitionCreateSerializer, SchemaDefinitionSerializer
from .services import SchemaService


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


class SchemaDefinitionDetailView(generics.RetrieveAPIView):
    queryset = SchemaDefinition.objects.all()
    serializer_class = SchemaDefinitionSerializer
