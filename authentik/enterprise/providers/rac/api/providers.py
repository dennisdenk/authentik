"""RAC Provider API Views"""
from django.core.cache import cache
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.rac.api.endpoints import EndpointSerializer
from authentik.enterprise.providers.rac.models import Endpoint, RACProvider
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


def user_endpoint_cache_key(user_pk: str) -> str:
    """Cache key where endpoint list for user is saved"""
    return f"goauthentik.io/providers/rac/endpoint_access/{user_pk}"


class RACProviderSerializer(ProviderSerializer):
    """RACProvider Serializer"""

    class Meta:
        model = RACProvider
        fields = ProviderSerializer.Meta.fields + [
            "protocol",
            "endpoints",
            "settings",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class RACProviderViewSet(UsedByMixin, ModelViewSet):
    """RACProvider Viewset"""

    queryset = RACProvider.objects.all()
    serializer_class = RACProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
    }
    search_fields = ["name", "protocol"]
    ordering = ["name", "protocol"]

    def _get_allowed_endpoints(self, queryset: QuerySet) -> list[Endpoint]:
        endpoints = []
        for endpoint in queryset:
            engine = PolicyEngine(endpoint, self.request.user, self.request)
            engine.build()
            if engine.passing:
                endpoints.append(endpoint)
        return endpoints

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
            )
        ],
        responses={
            200: EndpointSerializer(many=True),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(methods=["GET"], detail=True)
    def list_endpoints(self, request: Request, *args, **kwargs) -> Response:
        """List accessible endpoints"""
        should_cache = request.GET.get("search", "") == ""
        provider: RACProvider = self.get_object()

        queryset = self._filter_queryset_for_list(Endpoint.objects.filter(provider__in=[provider]))
        self.paginate_queryset(queryset)

        allowed_endpoints = []
        if not should_cache:
            allowed_endpoints = self._get_allowed_endpoints(queryset)
        if should_cache:
            allowed_endpoints = cache.get(user_endpoint_cache_key(self.request.user.pk))
            if not allowed_endpoints:
                LOGGER.debug("Caching allowed endpoint list")
                allowed_endpoints = self._get_allowed_endpoints(queryset)
                cache.set(
                    user_endpoint_cache_key(self.request.user.pk),
                    allowed_endpoints,
                    timeout=86400,
                )
        serializer = EndpointSerializer(allowed_endpoints, many=True)
        return self.get_paginated_response(serializer.data)
