"""Tryke fixtures for the ToGrill tests."""

from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, Mock, patch

from togrill_bluetooth.client import Client
from togrill_bluetooth.packets import Packet, PacketA0Notify, PacketNotify
from tryke import Depends, fixture

from homeassistant.components.togrill.const import (
    CONF_HAS_AMBIENT,
    CONF_PROBE_COUNT,
    DOMAIN,
)
from homeassistant.const import CONF_ADDRESS, CONF_MODEL

from . import TOGRILL_SERVICE_INFO

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth


@fixture
def mock_entry() -> MockConfigEntry:
    """Create hass config fixture."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: TOGRILL_SERVICE_INFO.address,
            CONF_MODEL: "Pro-05",
            CONF_PROBE_COUNT: 2,
        },
        unique_id=TOGRILL_SERVICE_INFO.address,
    )


@fixture
def mock_entry_with_ambient() -> MockConfigEntry:
    """Create hass config fixture with ambient sensor enabled."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: TOGRILL_SERVICE_INFO.address,
            CONF_MODEL: "Pro-05",
            CONF_PROBE_COUNT: 2,
            CONF_HAS_AMBIENT: True,
        },
        unique_id=TOGRILL_SERVICE_INFO.address,
    )


@fixture
def mock_unload_entry() -> Generator[AsyncMock]:
    """Override async_unload_entry."""
    with patch(
        "homeassistant.components.togrill.async_unload_entry",
        return_value=True,
    ) as mock_unload_entry:
        yield mock_unload_entry


@fixture
def mock_setup_entry(
    _unload: AsyncMock = Depends(mock_unload_entry),
) -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.togrill.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_client_class() -> Generator[Mock]:
    """Auto mock bluetooth client class."""
    with (
        patch(
            "homeassistant.components.togrill.config_flow.Client", autospec=True
        ) as client_class,
        patch("homeassistant.components.togrill.coordinator.Client", new=client_class),
    ):
        yield client_class


@fixture
def mock_client(
    _bluetooth: None = Depends(enable_bluetooth),
    client_class: Mock = Depends(mock_client_class),
) -> Mock:
    """Auto mock bluetooth client behavior."""
    client_object = Mock(spec=Client)
    client_object.mocked_notify = None

    async def _connect(
        address: str,
        callback: Callable[[Packet], None] | None = None,
        disconnected_callback: Callable[[], None] | None = None,
    ) -> Mock:
        client_object.mocked_notify = callback
        if disconnected_callback:

            def _disconnected_callback():
                client_object.is_connected = False
                disconnected_callback()

            client_object.mocked_disconnected_callback = _disconnected_callback
        return client_object

    async def _disconnect() -> None:
        pass

    async def _request(packet_type: type[Packet]) -> None:
        if packet_type is PacketA0Notify:
            client_object.mocked_notify(PacketA0Notify(0, 0, 0, 0, 0, False, 0, False))

    async def _read(packet_type: type[PacketNotify]) -> PacketNotify:
        if packet_type is PacketA0Notify:
            return PacketA0Notify(0, 0, 0, 0, 0, False, 0, False)
        raise NotImplementedError

    client_class.connect.side_effect = _connect
    client_object.request.side_effect = _request
    client_object.read.side_effect = _read
    client_object.disconnect.side_effect = _disconnect
    client_object.is_connected = True

    return client_object
