"""Tryke fixtures for the mqtt integration."""

from collections.abc import Generator
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import DATA_MQTT
from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceNotFound

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_mqtt_mock

_LOGGER = logging.getLogger(__name__)


@fixture
def _module_marker() -> None:
    """Sentinel fixture to keep the module non-empty."""
    return None


@fixture
async def mqtt_mock(hass: HomeAssistant = Depends(hass_fixture)) -> Any:
    """Set up MQTT and return the mocked client.

    Mirrors the pytest ``mqtt_mock`` fixture from ``tests/conftest.py``.
    Wraps the real ``MQTT`` client so tests can both exercise real
    publish/subscribe and assert on ``mqtt_mock.async_publish/async_subscribe``.
    """
    real_mqtt = mqtt.MQTT
    mock_mqtt_instance: MagicMock | None = None

    def create_mock_mqtt(*args: Any, **kwargs: Any) -> MagicMock:
        nonlocal mock_mqtt_instance
        real_instance = real_mqtt(*args, **kwargs)
        spec = [*dir(real_instance), "_mqttc"]
        mock_mqtt_instance = MagicMock(
            return_value=real_instance,
            spec_set=spec,
            wraps=real_instance,
        )
        return mock_mqtt_instance

    # Patch yaml config loader so MQTT setup doesn't fail looking for
    # tests/testing_config/configuration.yaml during fixture setup.
    with (
        patch("homeassistant.config.load_yaml_config_file", return_value={}),
        patch("homeassistant.components.mqtt.MQTT", side_effect=create_mock_mqtt),
    ):
        try:
            await setup_mqtt_mock(hass)
        except AttributeError:
            # Shim fails on ``entry.runtime_data`` access — MQTT stores its
            # client on ``hass.data[DATA_MQTT]`` instead.
            pass

    if mock_mqtt_instance is not None:
        mock_mqtt_instance.connected = True
        return mock_mqtt_instance

    mqtt_data = hass.data.get(DATA_MQTT)
    client = mqtt_data.client if mqtt_data is not None else None
    if client is not None:
        client.connected = True
    return client


@fixture
def service_calls(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[list[ServiceCall]]:
    """Track all service calls."""
    calls: list[ServiceCall] = []

    _original_async_call = hass.services.async_call

    async def _async_call(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        blocking: bool = False,
        context: Context | None = None,
        target: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> ServiceResponse:
        calls.append(
            ServiceCall(hass, domain, service, service_data, context, return_response)
        )
        try:
            return await _original_async_call(
                domain,
                service,
                service_data,
                blocking,
                context,
                target,
                return_response,
            )
        except ServiceNotFound:
            _LOGGER.debug("Ignoring unknown service call to %s.%s", domain, service)
        return None

    with patch("homeassistant.core.ServiceRegistry.async_call", _async_call):
        yield calls


@fixture
def tag_mock() -> Generator[AsyncMock]:
    """Fixture to mock the tag scanner."""
    with patch("homeassistant.components.tag.async_scan_tag") as mock_tag:
        yield mock_tag
