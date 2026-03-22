from django.urls import path

from .views import (
    ActivateConfigVersionView,
    ConfigItemDetailView,
    ConfigItemListCreateView,
    ConfigVersionDetailView,
    ConfigVersionListCreateView,
    ResolvedConfigView,
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

    # Resolved config
    path("resolved-config/", ResolvedConfigView.as_view(), name="resolved-config"),
]
