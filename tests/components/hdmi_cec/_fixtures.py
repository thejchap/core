"""Tryke fixtures for HDMI-CEC tests."""

from collections.abc import Callable, Coroutine, Generator
from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.hdmi_cec import DOMAIN
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

type CecEntityCreator = Callable[..., Coroutine[Any, Any, None]]
type HDMINetworkCreator = Callable[..., Coroutine[Any, Any, MagicMock]]


@fixture
def mock_cec_adapter() -> Generator[MagicMock]:
    """Mock CecAdapter.

    Always mocked as it imports the `cec` library which is part of `libcec`.
    """
    with patch(
        "homeassistant.components.hdmi_cec.CecAdapter", autospec=True
    ) as mock_cec_adapter:
        yield mock_cec_adapter


@fixture
def mock_hdmi_network() -> Generator[MagicMock]:
    """Mock HDMINetwork."""
    with patch(
        "homeassistant.components.hdmi_cec.HDMINetwork", autospec=True
    ) as mock_hdmi_network:
        yield mock_hdmi_network


@fixture
def mock_tcp_adapter() -> Generator[MagicMock]:
    """Mock TcpAdapter."""
    with patch(
        "homeassistant.components.hdmi_cec.TcpAdapter", autospec=True
    ) as mock_tcp_adapter:
        yield mock_tcp_adapter


@fixture
def create_hdmi_network(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hdmi_network: MagicMock = Depends(mock_hdmi_network),
    _mock_cec_adapter: MagicMock = Depends(mock_cec_adapter),
) -> HDMINetworkCreator:
    """Create an initialized mock hdmi_network."""

    async def hdmi_network(config: dict[str, Any] | None = None) -> MagicMock:
        if not config:
            config = {}
        await async_setup_component(hass, DOMAIN, {DOMAIN: config})

        mock_hdmi_network_instance = mock_hdmi_network.return_value

        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()
        return mock_hdmi_network_instance

    return hdmi_network


@fixture
def create_cec_entity(
    hass: HomeAssistant = Depends(hass_fixture),
) -> CecEntityCreator:
    """Create a CecEntity."""

    async def cec_entity(hdmi_network: MagicMock, device: Any) -> None:
        new_device_callback = hdmi_network.set_new_device_callback.call_args.args[0]
        new_device_callback(device)
        await hass.async_block_till_done()

    return cec_entity
