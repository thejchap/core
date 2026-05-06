"""Test the IKEA Idasen Desk config flow."""

from unittest.mock import ANY, MagicMock, patch

from bleak.exc import BleakError
from idasen_ha.errors import AuthFailedError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.idasen_desk.const import DOMAIN
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import IDASEN_DISCOVERY_INFO, NOT_IDASEN_DISCOVERY_INFO
from ._fixtures import mock_bluetooth_setup, mock_desk_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bt: None = Depends(enable_bluetooth),
    _bt_setup: None = Depends(mock_bluetooth_setup),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _desk_api: MagicMock = Depends(mock_desk_api),
) -> None:
    """Test user step success path."""
    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[NOT_IDASEN_DISCOVERY_INFO, IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(IDASEN_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal(
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        }
    )
    expect(result2["result"].unique_id).to_equal(IDASEN_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _desk_api: MagicMock = Depends(mock_desk_api),
) -> None:
    """Test user step replaces ignored devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=IDASEN_DISCOVERY_INFO.address,
        source=config_entries.SOURCE_IGNORE,
        data={CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[NOT_IDASEN_DISCOVERY_INFO, IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(IDASEN_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal(
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        }
    )
    expect(result2["result"].unique_id).to_equal(IDASEN_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with no devices found."""
    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[NOT_IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_no_new_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with only existing devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        },
        unique_id=IDASEN_DISCOVERY_INFO.address,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.cases(
    test.case("timeout", exception=TimeoutError, expected_error="cannot_connect"),
    test.case("bleak_error", exception=BleakError, expected_error="cannot_connect"),
    test.case("auth_failed", exception=AuthFailedError, expected_error="auth_failed"),
    test.case("runtime_error", exception=RuntimeError, expected_error="unknown"),
)
async def user_step_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    desk_api: MagicMock = Depends(mock_desk_api),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test user step with a cannot connect error."""
    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    default_connect_side_effect = desk_api.connect.side_effect
    desk_api.connect.side_effect = exception

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": expected_error})

    desk_api.connect.side_effect = default_connect_side_effect
    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(IDASEN_DISCOVERY_INFO.name)
    expect(result3["data"]).to_equal(
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        }
    )
    expect(result3["result"].unique_id).to_equal(IDASEN_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def bluetooth_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    desk_api: MagicMock = Depends(mock_desk_api),
) -> None:
    """Test bluetooth step success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=IDASEN_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(IDASEN_DISCOVERY_INFO.name)
    expect(result2["data"]).to_equal(
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        }
    )
    expect(result2["result"].unique_id).to_equal(IDASEN_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    desk_api.connect.assert_called_with(ANY, retry=False)
