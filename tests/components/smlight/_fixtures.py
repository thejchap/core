"""Tryke fixtures for the SMLIGHT integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pysmlight.exceptions import SmlightAuthError
from pysmlight.sse import sseClient
from pysmlight.web import ActionWrapper, CmdWrapper, Firmware, Info, Sensors
from tryke import fixture

from homeassistant.components.smlight.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)

MOCK_DEVICE_NAME = "slzb-06"
MOCK_HOST = "192.168.1.161"
MOCK_HOSTNAME = "slzb-06p7.lan"
MOCK_USERNAME = "test-user"
MOCK_PASSWORD = "test-pass"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
        unique_id="aa:bb:cc:dd:ee:ff",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.smlight.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_smlight_client() -> Generator[MagicMock]:
    """Mock the SMLIGHT API client."""
    with (
        patch("homeassistant.components.smlight.Api2", autospec=True) as smlight_mock,
        patch("homeassistant.components.smlight.config_flow.Api2", new=smlight_mock),
    ):
        api = smlight_mock.return_value
        api.host = MOCK_HOST

        def get_info_side_effect(*args, **kwargs) -> Info:
            """Return the info."""
            if api.check_auth_needed.return_value and not api.authenticate.called:
                raise SmlightAuthError

            return Info.from_dict(load_json_object_fixture("info.json", DOMAIN))

        api.get_info.side_effect = get_info_side_effect

        api.get_sensors.return_value = Sensors.from_dict(
            load_json_object_fixture("sensors.json", DOMAIN)
        )

        def get_firmware_side_effect(*args, **kwargs) -> list[Firmware]:
            """Return the firmware version."""
            fw_list = []
            if kwargs.get("mode") == "zigbee":
                if kwargs.get("zb_type") == 0:
                    fw_list = load_json_array_fixture("zb_firmware.json", DOMAIN)
                else:
                    fw_list = load_json_array_fixture("zb_firmware_router.json", DOMAIN)
            else:
                fw_list = load_json_array_fixture("esp_firmware.json", DOMAIN)

            return [Firmware.from_dict(fw) for fw in fw_list]

        api.get_firmware_version.side_effect = get_firmware_side_effect

        api.check_auth_needed.return_value = False
        api.authenticate.return_value = True

        api.actions = AsyncMock(spec_set=ActionWrapper)
        api.actions.ambilight = AsyncMock(return_value=True)
        api.cmds = AsyncMock(spec_set=CmdWrapper)
        api.set_toggle = AsyncMock()
        api.sse = MagicMock(spec_set=sseClient)

        yield api
