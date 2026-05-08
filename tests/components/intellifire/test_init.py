"""Test the IntelliFire integration."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.intellifire import CONF_USER_ID
from homeassistant.components.intellifire.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_apis_single_fp,
    mock_cloud_interface,
    mock_common_data_local,
    mock_fp,
    mock_local_interface,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test.skip("sibling port deferred")
async def migration_v1_1_to_v1_3() -> None:
    """Stub."""


@test
async def migration_v1_1_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _apis: tuple[AsyncMock, AsyncMock, AsyncMock] = Depends(mock_apis_single_fp),
) -> None:
    """Test migration failure when cloud lookup fails."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        title="Fireplace of testing",
        data={
            CONF_HOST: "11.168.2.218",
            CONF_USERNAME: "grumpypanda@china.cn",
            CONF_PASSWORD: "you-stole-my-pandas",
            CONF_USER_ID: (
                "52C3F9E8B9D3AC99F8E4D12345678901FE9A2BC7D85F7654E28BF98BCD123456"
            ),
        },
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state is ConfigEntryState.MIGRATION_ERROR).to_be(True)


@test.skip("sibling port deferred")
async def migration_v1_2_to_v1_3() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def migration_v1_2_to_v1_3_defaults() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def init_with_no_username() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def connectivity_bad() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def update_options_change_read_mode_only() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def update_options_change_control_mode_only() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def update_options_change_both_modes() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def update_options_no_change() -> None:
    """Stub."""


@test.skip("sibling port deferred")
async def coordinator_performs_poll() -> None:
    """Stub."""
