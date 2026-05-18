"""Tryke fixtures for the humidifier tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.humidifier import DOMAIN, HumidifierEntity
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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
async def target_humidifiers(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple humidifier entities associated with different targets."""
    return await target_entities(hass, "humidifier")


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
