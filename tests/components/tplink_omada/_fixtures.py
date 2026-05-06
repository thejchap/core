"""Tryke fixtures for the tplink_omada integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tplink_omada_client import OmadaSite
from tplink_omada_client.devices import (
    OmadaFirmwareUpdate,
    OmadaGateway,
    OmadaListDevice,
    OmadaSwitch,
    OmadaSwitchPortDetails,
)
from tryke import Depends, fixture

from homeassistant.components.tplink_omada.config_flow import CONF_SITE
from homeassistant.components.tplink_omada.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant

from tests.common import (
    MockConfigEntry,
    async_load_json_array_fixture,
    async_load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Test Omada Controller",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "mocked-password",
            CONF_USERNAME: "mocked-user",
            CONF_VERIFY_SSL: False,
            CONF_SITE: "Default",
        },
        unique_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.tplink_omada.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
async def mock_omada_site_client(
    hass: HomeAssistant = Depends(hass_fx),
) -> AsyncMock:
    """Mock Omada site client."""
    site_client = MagicMock()

    gateway_data = await async_load_json_object_fixture(
        hass, "gateway-TL-ER7212PC.json", DOMAIN
    )
    gateway = OmadaGateway(gateway_data)
    site_client.get_gateway = AsyncMock(return_value=gateway)

    switch1_data = await async_load_json_object_fixture(
        hass, "switch-TL-SG3210XHP-M2.json", DOMAIN
    )
    switch1 = OmadaSwitch(switch1_data)
    site_client.get_switches = AsyncMock(return_value=[switch1])
    site_client.get_switch = AsyncMock(return_value=switch1)

    devices_data = await async_load_json_array_fixture(hass, "devices.json", DOMAIN)
    devices = [OmadaListDevice(d) for d in devices_data]
    site_client.get_devices = AsyncMock(return_value=devices)

    switch1_ports_data = await async_load_json_array_fixture(
        hass, "switch-ports-TL-SG3210XHP-M2.json", DOMAIN
    )
    switch1_ports = [OmadaSwitchPortDetails(p) for p in switch1_ports_data]
    site_client.get_switch_ports = AsyncMock(return_value=switch1_ports)

    async def get_firmware_details(
        device: OmadaListDevice,
    ) -> OmadaFirmwareUpdate | None:
        if device.need_upgrade:
            firmware_data = await async_load_json_object_fixture(
                hass, f"firmware-update-{device.mac}.json", DOMAIN
            )
            return OmadaFirmwareUpdate(firmware_data)
        return None

    site_client.get_firmware_details = AsyncMock(side_effect=get_firmware_details)
    site_client.start_firmware_upgrade = AsyncMock()

    async def async_empty() -> AsyncGenerator:
        for c in ():
            yield c

    site_client.get_known_clients.return_value = async_empty()
    site_client.get_connected_clients.return_value = async_empty()
    site_client.reconnect_client = AsyncMock()
    return site_client


@fixture
def mock_omada_client(
    site_client: AsyncMock = Depends(mock_omada_site_client),
) -> Generator[MagicMock]:
    """Mock Omada client."""
    with (
        patch(
            "homeassistant.components.tplink_omada.create_omada_client",
            autospec=True,
        ) as client_mock,
        patch(
            "homeassistant.components.tplink_omada.config_flow.create_omada_client",
            new=client_mock,
        ),
    ):
        client = client_mock.return_value

        client.get_site_client.return_value = site_client
        client.login.return_value = "12345"
        client.get_controller_name.return_value = "OC200"
        client.get_sites.return_value = [OmadaSite("Display Name", "SiteId")]
        yield client
