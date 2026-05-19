"""Tryke fixtures for zone tests."""

from collections.abc import Awaitable, Callable, Generator
import logging
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components import zone
from homeassistant.components.zone import DOMAIN
from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceNotFound
from homeassistant.setup import async_setup_component

from tests.common import mock_component
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)

_LOGGER = logging.getLogger(__name__)


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
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Initialize components."""
    mock_component(hass, "group")
    await async_setup_component(
        hass,
        zone.DOMAIN,
        {
            "zone": {
                "name": "test",
                "latitude": 32.880837,
                "longitude": -117.237561,
                "radius": 250,
            }
        },
    )


@fixture
def storage_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> Callable[..., Awaitable[bool]]:
    """Storage setup."""

    async def _storage(
        items: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> bool:
        if items is None:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {
                    "items": [
                        {
                            "id": "from_storage",
                            "name": "from storage",
                            "latitude": 1,
                            "longitude": 2,
                            "radius": 3,
                            "passive": False,
                            "icon": "mdi:from-storage",
                        }
                    ]
                },
            }
        else:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": items},
            }
        if config is None:
            config = {}
        return await async_setup_component(hass, DOMAIN, config)

    return _storage
