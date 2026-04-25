"""Tryke fixtures for the Airzone Cloud integration."""

from collections.abc import Generator
from unittest.mock import patch

from aioairzone_cloud.cloudapi import AirzoneCloudApi
from tryke import fixture


class _MockAirzoneCloudApi(AirzoneCloudApi):
    """Mock AirzoneCloudApi class."""

    async def mock_update(self) -> None:
        """Mock AirzoneCloudApi _update function."""
        await self.update_polling()


@fixture
def airzone_cloud_no_websockets() -> Generator[None]:
    """Disable Airzone Cloud WebSockets."""
    with (
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi._update",
            side_effect=_MockAirzoneCloudApi.mock_update,
            autospec=True,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.connect_installation_websockets",
            return_value=None,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.update_websockets",
            return_value=None,
        ),
    ):
        yield
