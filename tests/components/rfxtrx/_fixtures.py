"""Tryke fixtures for rfxtrx tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from freezegun import freeze_time
from RFXtrx import Connect, RFXtrxTransport
from tryke import Depends, fixture

from homeassistant.components import rfxtrx
from homeassistant.components.rfxtrx import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture


def create_rfx_test_cfg(
    device: str = "abcd",
    automatic_add: bool = False,
    protocols: list[str] | None = None,
    devices: dict[str, dict] | None = None,
    host: str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """Create rfxtrx config entry data."""
    return {
        "device": device,
        "host": host,
        "port": port,
        "automatic_add": automatic_add,
        "protocols": protocols,
        "debug": False,
        "devices": devices or {},
    }


async def setup_rfx_test_cfg(
    hass: HomeAssistant,
    device: str = "abcd",
    automatic_add: bool = False,
    devices: dict[str, dict] | None = None,
    protocols: list[str] | None = None,
    host: str | None = None,
    port: int | None = None,
) -> MockConfigEntry:
    """Construct a rfxtrx config entry."""
    entry_data = create_rfx_test_cfg(
        device=device,
        automatic_add=automatic_add,
        devices=devices,
        protocols=protocols,
        host=host,
        port=port,
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)
    mock_entry.supports_remove_device = True
    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()
    return mock_entry


@fixture
def transport_mock() -> Generator[Mock]:
    """Fixture that make sure all transports are fake."""
    transport = Mock(spec=RFXtrxTransport)
    with (
        patch("RFXtrx.PySerialTransport", new=transport),
        patch("RFXtrx.PyNetworkTransport", transport),
    ):
        yield transport


@fixture
def connect_mock(
    _transport: Mock = Depends(transport_mock),
) -> Generator[MagicMock]:
    """Fixture that make sure connect class is mocked."""
    with patch("RFXtrx.Connect") as connect:
        yield connect


@fixture
def rfxtrx_fx(
    hass: HomeAssistant = Depends(hass_fixture),
    connect_mock: MagicMock = Depends(connect_mock),
) -> Mock:
    """Fixture that cleans up threads from integration."""
    rfx = Mock(spec=Connect)

    def _init(transport, event_callback=None, modes=None):
        rfx.event_callback = event_callback
        rfx.transport = transport
        return rfx

    connect_mock.side_effect = _init

    async def _signal_event(packet_id: str) -> Any:
        event = rfxtrx.get_rfx_object(packet_id)
        await hass.async_add_executor_job(
            rfx.event_callback,
            event,
        )

        await hass.async_block_till_done()
        await hass.async_block_till_done()
        return event

    rfx.signal = _signal_event
    return rfx


@fixture
async def rfxtrx_automatic_fx(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx_fx: Mock = Depends(rfxtrx_fx),
) -> AsyncGenerator[Mock]:
    """Fixture that starts up with automatic additions."""
    await setup_rfx_test_cfg(hass, automatic_add=True, devices={})
    yield rfxtrx_fx


@fixture
def timestep_fx(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[Callable[[int], Coroutine[Any, Any, None]]]:
    """Step system time forward."""
    with freeze_time(utcnow()) as frozen_time:

        async def delay(seconds: int) -> None:
            """Trigger delay in system."""
            frozen_time.tick(delta=seconds)
            async_fire_time_changed(hass)
            await hass.async_block_till_done()

        yield delay
