"""Testing the Prowl initialisation."""

from unittest.mock import AsyncMock

import prowlpy
from tryke import Depends, expect, fixture, test

from homeassistant.components import notify
from homeassistant.components.prowl.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    ENTITY_ID,
    TEST_API_KEY,
    configure_prowl_through_yaml,
    mock_prowlpy,
    mock_prowlpy_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_reload_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_prowlpy_config_entry: MockConfigEntry = Depends(mock_prowlpy_config_entry),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Test the Prowl configuration entry loading/reloading/unloading."""
    mock_prowlpy_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_prowlpy_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_prowlpy_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)

    await hass.config_entries.async_reload(mock_prowlpy_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_prowlpy_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_prowlpy_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(mock_prowlpy_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "timeout",
        prowlpy_side_effect=TimeoutError,
        expected_config_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "invalid_api_key",
        prowlpy_side_effect=prowlpy.APIError(f"Invalid API key: {TEST_API_KEY}"),
        expected_config_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "rate_limit",
        prowlpy_side_effect=prowlpy.APIError("Not accepted: exceeded rate limit"),
        expected_config_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "internal_server_error",
        prowlpy_side_effect=prowlpy.APIError("Internal server error"),
        expected_config_state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def config_entry_failures(
    *,
    prowlpy_side_effect: Exception | type[Exception],
    expected_config_state: ConfigEntryState,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_prowlpy_config_entry: MockConfigEntry = Depends(mock_prowlpy_config_entry),
    mock_prowlpy: AsyncMock = Depends(mock_prowlpy),
) -> None:
    """Test the Prowl configuration entry dealing with bad API key."""
    mock_prowlpy.verify_key.side_effect = prowlpy_side_effect

    mock_prowlpy_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_prowlpy_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_prowlpy_config_entry.state).to_be(expected_config_state)
    expect(mock_prowlpy.verify_key.call_count > 0).to_be(True)


@test
async def both_yaml_and_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    _configure_yaml: None = Depends(configure_prowl_through_yaml),
    mock_prowlpy_config_entry: MockConfigEntry = Depends(mock_prowlpy_config_entry),
) -> None:
    """Test having both YAML config and a config entry works."""
    mock_prowlpy_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_prowlpy_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_prowlpy_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(hass.services.has_service(notify.DOMAIN, DOMAIN)).to_be(True)
    expect(hass.states.get(ENTITY_ID) is not None).to_be(True)
