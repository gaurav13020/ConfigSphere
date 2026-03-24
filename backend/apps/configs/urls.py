from django.urls import path

from .views import (
    ActivateConfigVersionView,
    ArchiveConfigVersionView,
    ConfigItemDetailView,
    ConfigItemListCreateView,
    ConfigVersionDetailView,
    ConfigVersionListCreateView,
    ResolvedConfigView,
    ValidateConfigVersionView,
)

urlpatterns = [
    # Config items
    path("config-items/", ConfigItemListCreateView.as_view(), name="config-item-list-create"),
    path("config-items/<int:pk>/", ConfigItemDetailView.as_view(), name="config-item-detail"),

    # Config versions (nested under item)
    path("config-items/<int:item_pk>/versions/", ConfigVersionListCreateView.as_view(), name="config-version-list-create"),

    # Config version standalone (for activation and detail)
    path("config-versions/<int:pk>/", ConfigVersionDetailView.as_view(), name="config-version-detail"),
    path("config-versions/<int:pk>/activate/", ActivateConfigVersionView.as_view(), name="config-version-activate"),
    path("config-versions/<int:pk>/validate/", ValidateConfigVersionView.as_view(), name="config-version-validate"),
    path("config-versions/<int:pk>/archive/", ArchiveConfigVersionView.as_view(), name="config-version-archive"),

    # Resolved config
    path("resolved-config/", ResolvedConfigView.as_view(), name="resolved-config"),
]
