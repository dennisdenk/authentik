"""RAC Provider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.rac.models import Endpoint


class EndpointSerializer(ModelSerializer):
    """Endpoint Serializer"""

    class Meta:
        model = Endpoint
        fields = ["pk", "name", "protocol", "host", "settings", "property_mappings", "auth_mode"]


class EndpointViewSet(UsedByMixin, ModelViewSet):
    """Endpoint Viewset"""

    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer
    search_fields = ["name", "protocol"]
    ordering = ["name", "protocol"]
