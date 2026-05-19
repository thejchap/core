"""Tryke fixtures for the sun integration tests."""

from collections.abc import Generator
import logging
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceNotFound

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock

_LOGGER = logging.getLogger(__name__)


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


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
