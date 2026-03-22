from django.urls import path

from .views import SchemaDefinitionDetailView, SchemaDefinitionListCreateView

urlpatterns = [
    path("schemas/", SchemaDefinitionListCreateView.as_view(), name="schema-list-create"),
    path("schemas/<int:pk>/", SchemaDefinitionDetailView.as_view(), name="schema-detail"),
]
