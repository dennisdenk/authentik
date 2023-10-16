"""RAC Models"""
from typing import Optional

from django.db import models
from django.urls import reverse
from rest_framework.serializers import Serializer

from authentik.core.models import Provider


class Protocols(models.TextChoices):
    """Supported protocols"""

    RDP = "rdp"
    VNC = "vnc"
    SSH = "ssh"


class AuthenticationMode(models.TextChoices):
    """Authentication modes"""

    STATIC = "static"
    PROMPT = "prompt"


class RACProvider(Provider):
    """Remote access provider"""

    protocol = models.TextField(choices=Protocols.choices)
    host = models.TextField()
    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(choices=AuthenticationMode.choices)

    @property
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        try:
            # pylint: disable=no-member
            return reverse(
                "authentik_enterprise_rac:if-rac",
                kwargs={"app": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    def get_settings(self) -> dict:
        """Get settings"""
        settings = self.settings.copy()
        settings["hostname"] = self.host
        settings["enable-drive"] = "true"
        settings["drive-name"] = "authentik"
        settings["client-name"] = "foo"
        if self.protocol == Protocols.RDP:
            settings["resize-method"] = "display-update"
            settings["enable-wallpaper"] = "true"
            settings["enable-font-smoothing"] = "true"
            # params["enable-theming"] = "true"
            # params["enable-full-window-drag"] = "true"
            # params["enable-desktop-composition"] = "true"
            # params["enable-menu-animations"] = "true"
            # params["enable-audio-input"] = "true"
        return settings

    @property
    def component(self) -> str:
        return "ak-provider-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.rac.api.providers import RACProviderSerializer

        return RACProviderSerializer
