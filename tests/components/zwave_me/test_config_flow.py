"""Test the zwave_me config flow."""

from ipaddress import ip_address
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.zwave_me.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.14"),
    ip_addresses=[ip_address("192.168.1.14")],
    hostname="mock_hostname",
    name="mock_name",
    port=1234,
    properties={
        "deviceid": "aa:bb:cc:dd:ee:ff",
        "manufacturer": "fake_manufacturer",
        "model": "fake_model",
        "serialNumber": "fake_serial",
    },
    type="mock_type",
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    with (
        patch(
            "homeassistant.components.zwave_me.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.zwave_me.helpers.get_uuid",
            return_value="test_uuid",
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "192.168.1.14",
                "token": "test-token",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("ws://192.168.1.14")
    expect(result2["data"]).to_equal(
        {
            "url": "ws://192.168.1.14",
            "token": "test-token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow from zeroconf."""
    with (
        patch(
            "homeassistant.components.zwave_me.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.zwave_me.helpers.get_uuid",
            return_value="test_uuid",
        ),
    ):
        result: FlowResult = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=MOCK_ZEROCONF_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "token": "test-token",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("ws://192.168.1.14")
    expect(result2["data"]).to_equal(
        {
            "url": "ws://192.168.1.14",
            "token": "test-token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def error_handling_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting proper errors from no uuid."""
    with patch("homeassistant.components.zwave_me.helpers.get_uuid", return_value=None):
        result: FlowResult = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=MOCK_ZEROCONF_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_valid_uuid_set")


@test
async def handle_error_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting proper errors from no uuid."""
    with patch("homeassistant.components.zwave_me.helpers.get_uuid", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "192.168.1.15",
                "token": "test-token",
            },
        )
        expect(result2["errors"]).to_equal({"base": "no_valid_uuid_set"})


@test
async def duplicate_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting proper errors from duplicate uuid."""
    entry: MockConfigEntry = MockConfigEntry(
        domain=DOMAIN,
        title="ZWave_me",
        data={
            "url": "ws://192.168.1.15",
            "token": "test-token",
        },
        unique_id="test_uuid",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.zwave_me.helpers.get_uuid",
        return_value="test_uuid",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "192.168.1.15",
                "token": "test-token",
            },
        )
        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def duplicate_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting proper errors from duplicate uuid."""
    entry: MockConfigEntry = MockConfigEntry(
        domain=DOMAIN,
        title="ZWave_me",
        data={
            "url": "ws://192.168.1.14",
            "token": "test-token",
        },
        unique_id="test_uuid",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.zwave_me.helpers.get_uuid",
        return_value="test_uuid",
    ):
        result: FlowResult = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=MOCK_ZEROCONF_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
