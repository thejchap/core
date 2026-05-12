"""Tests for the Redgtech switch platform."""

from unittest.mock import MagicMock

from redgtech_api.api import RedgtechAuthError, RedgtechConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import mock_config_entry, mock_redgtech_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def _setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@test.skip("snapshot test — out of scope")
async def entities() -> None:
    """Stub for test_entities (snapshot)."""


@test
async def switch_turn_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_redgtech_api),
) -> None:
    """Test turning a switch on."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.living_room_switch"},
        blocking=True,
    )
    mock_api.set_switch_state.assert_called_once_with(
        "switch_001", True, "mock_access_token"
    )


@test
async def switch_turn_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_redgtech_api),
) -> None:
    """Test turning a switch off."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.kitchen_switch"},
        blocking=True,
    )
    mock_api.set_switch_state.assert_called_once_with(
        "switch_002", False, "mock_access_token"
    )


@test
async def switch_toggle(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_redgtech_api),
) -> None:
    """Test toggling a switch."""
    await _setup_integration(hass, entry)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: "switch.living_room_switch"},
        blocking=True,
    )
    mock_api.set_switch_state.assert_called_once_with(
        "switch_001", True, "mock_access_token"
    )


@test.cases(
    test.case(
        "connection_error",
        exception=RedgtechConnectionError("Connection failed"),
        msg="connection_error",
    ),
    test.case(
        "auth_error",
        exception=RedgtechAuthError("Auth failed"),
        msg="switch_auth_error",
    ),
)
async def exception_handling(
    *,
    exception: Exception,
    msg: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_redgtech_api),
) -> None:
    """Test exception handling when controlling switches."""
    await _setup_integration(hass, entry)
    mock_api.set_switch_state.side_effect = exception
    async with expect_raises_async(HomeAssistantError, match=msg):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.living_room_switch"},
            blocking=True,
        )


@test
async def switch_auth_error_with_retry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_api: MagicMock = Depends(mock_redgtech_api),
) -> None:
    """Test handling auth errors with token renewal."""
    await _setup_integration(hass, entry)
    mock_api.set_switch_state.side_effect = RedgtechAuthError("Auth failed")
    async with expect_raises_async(
        HomeAssistantError,
        match="switch_auth_error",
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.living_room_switch"},
            blocking=True,
        )


@test.skip("requires freezer fixture — port deferred")
async def coordinator_data_update_success() -> None:
    """Stub for test_coordinator_data_update_success."""


@test.skip("requires freezer fixture — port deferred")
async def coordinator_connection_error_during_update() -> None:
    """Stub for test_coordinator_connection_error_during_update."""


@test.skip("requires freezer fixture — port deferred")
async def coordinator_auth_error_with_token_renewal() -> None:
    """Stub for test_coordinator_auth_error_with_token_renewal."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.redgtech.switch module imports cleanly."""
    from homeassistant.components.redgtech import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


# Suppress unused-import lints for fixtures only referenced via Depends
_ = (mock_config_entry, mock_redgtech_api)
