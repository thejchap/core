"""Tests for the Duco integration setup."""

from ssl import SSLContext
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from duco.exceptions import DucoConnectionError, DucoError
from duco.models import BoardInfo, DiagComponent, DiagStatus, LanInfo, Node
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    TEST_HOST,
    mock_board_info,
    mock_config_entry,
    mock_duco_client,
    mock_lan_info,
    mock_nodes,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.cases(
    test.case(
        "board_conn",
        method="async_get_board_info",
        exception=DucoConnectionError("Connection refused"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "board_err",
        method="async_get_board_info",
        exception=DucoError("Unexpected API error"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "nodes_conn",
        method="async_get_nodes",
        exception=DucoConnectionError("Connection refused"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_duco_client),
    *,
    method: str,
    exception: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test that fetch errors during setup result in the correct state."""
    target = client
    for part in method.split("."):
        target = getattr(target, part)
    target.side_effect = exception
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(expected_state)


@test
async def setup_entry_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_duco_client),
) -> None:
    """Test successful setup of the Duco integration."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_duco_client),
) -> None:
    """Test unloading the Duco integration."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_entry_builds_ssl_context_in_executor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    board_info: BoardInfo = Depends(mock_board_info),
    lan_info: LanInfo = Depends(mock_lan_info),
    nodes: list[Node] = Depends(mock_nodes),
) -> None:
    """Test that build_ssl_context runs in an executor and is passed to DucoClient."""
    mock_ssl_context = MagicMock(spec=SSLContext)
    with (
        patch(
            "homeassistant.components.duco.build_ssl_context",
            return_value=mock_ssl_context,
        ) as mock_build,
        patch(
            "homeassistant.components.duco.DucoClient",
            autospec=True,
        ) as mock_client_class,
    ):
        mock_client_class.return_value.async_get_board_info.return_value = board_info
        mock_client_class.return_value.async_get_lan_info.return_value = lan_info
        mock_client_class.return_value.async_get_nodes.return_value = nodes
        mock_client_class.return_value.async_get_diagnostics.return_value = [
            DiagComponent(component="Ventilation", status=DiagStatus.OK)
        ]
        mock_client_class.return_value.async_get_write_req_remaining.return_value = 100
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mock_build.assert_called_once()
    mock_client_class.assert_called_once_with(
        session=ANY,
        host=TEST_HOST,
        ssl_context=mock_ssl_context,
    )
