"""Tryke fixtures for Duco."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from duco.models import (
    BoardInfo,
    DiagComponent,
    DiagStatus,
    LanInfo,
    Node,
    NodeGeneralInfo,
    NodeSensorInfo,
    NodeVentilationInfo,
)
from tryke import Depends, fixture

from homeassistant.components.duco.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry

TEST_HOST = "192.168.1.100"
TEST_MAC = "aa:bb:cc:dd:ee:ff"

USER_INPUT = {CONF_HOST: TEST_HOST}


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="SILENT_CONNECT",
        domain=DOMAIN,
        data=USER_INPUT,
        unique_id=TEST_MAC,
    )


@fixture
def mock_board_info() -> BoardInfo:
    """Return mock board info."""
    return BoardInfo(
        box_name="SILENT_CONNECT",
        box_sub_type_name="Eu",
        serial_board_box="ABC123",
        serial_board_comm="DEF456",
        serial_duco_box="GHI789",
        serial_duco_comm="JKL012",
        time=1700000000,
    )


@fixture
def mock_lan_info() -> LanInfo:
    """Return mock LAN info."""
    return LanInfo(
        mode="WIFI_CLIENT",
        ip=TEST_HOST,
        net_mask="255.255.255.0",
        default_gateway="192.168.1.1",
        dns="8.8.8.8",
        mac=TEST_MAC,
        host_name="duco-box",
        rssi_wifi=-60,
    )


@fixture
def mock_nodes() -> list[Node]:
    """Return a list of nodes covering all supported types."""
    return [
        Node(
            node_id=1,
            general=NodeGeneralInfo(
                node_type="BOX",
                sub_type=1,
                network_type="VIRT",
                parent=0,
                asso=0,
                name="Living",
                identify=0,
            ),
            ventilation=NodeVentilationInfo(
                state="AUTO",
                time_state_remain=0,
                time_state_end=0,
                mode="AUTO",
                flow_lvl_tgt=0,
            ),
            sensor=NodeSensorInfo(
                co2=None,
                iaq_co2=None,
                rh=None,
                iaq_rh=None,
            ),
        ),
    ]


@fixture
def mock_duco_client(
    mock_board_info: BoardInfo = Depends(mock_board_info),
    mock_lan_info: LanInfo = Depends(mock_lan_info),
    mock_nodes: list[Node] = Depends(mock_nodes),
) -> Generator[AsyncMock]:
    """Return a mocked DucoClient used by both the integration and config flow."""
    with (
        patch(
            "homeassistant.components.duco.DucoClient",
            autospec=True,
        ) as mock_class,
        patch(
            "homeassistant.components.duco.config_flow.DucoClient",
            new=mock_class,
        ),
    ):
        client = mock_class.return_value
        client.async_get_board_info.return_value = mock_board_info
        client.async_get_lan_info.return_value = mock_lan_info
        client.async_get_nodes.return_value = mock_nodes
        client.async_get_diagnostics.return_value = [
            DiagComponent(component="Ventilation", status=DiagStatus.OK)
        ]
        client.async_get_write_req_remaining.return_value = 100
        yield client


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.duco.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
