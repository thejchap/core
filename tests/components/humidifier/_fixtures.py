"""Tryke fixtures for the humidifier tests."""

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.humidifier import DOMAIN, HumidifierEntity
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import Context, HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.exceptions import ServiceNotFound

from tests.common import (
    MockConfigEntry,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
    setup_test_component_platform,
)
from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock

_LOGGER = logging.getLogger(__name__)


TEST_DOMAIN = "test"


class _MockFlow(ConfigFlow):
    """Test flow."""


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
def service_calls(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[list[ServiceCall]]:
    """Track all service calls."""
    calls: list[ServiceCall] = []

    _original_async_call = hass.services.async_call

    async def _async_call(
        self: Any,
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
async def target_humidifiers(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple humidifier entities associated with different targets."""
    return await target_entities(hass, "humidifier")


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


async def setup_test_integration(
    hass: HomeAssistant,
    entities: list[HumidifierEntity],
) -> MockConfigEntry:
    """Set up a mocked test integration with the humidifier platform.

    Replacement for the ``register_test_integration`` + ``config_flow_fixture``
    pair from the original pytest conftest.
    """
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    cm = mock_config_flow(TEST_DOMAIN, _MockFlow)
    cm.__enter__()

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)

    async def help_async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.HUMIDIFIER]
        )
        return True

    async def help_async_unload_entry(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Unload test config entry."""
        return await hass.config_entries.async_unload_platforms(
            config_entry, [Platform.HUMIDIFIER]
        )

    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )

    setup_test_component_platform(
        hass,
        DOMAIN,
        entities=entities,
        from_config_entry=True,
    )
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
