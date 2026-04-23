"""Test the Ness Alarm config flow."""

from __future__ import annotations

from types import MappingProxyType
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.ness_alarm.const import (
    CONF_INFER_ARMING_STATE,
    CONF_SHOW_HOME_MODE,
    CONF_ZONE_ID,
    CONF_ZONE_NAME,
    CONF_ZONE_NUMBER,
    CONF_ZONE_TYPE,
    CONF_ZONES,
    DOMAIN,
    SUBENTRY_TYPE_ZONE,
)
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER, ConfigSubentry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ness_alarm._fixtures import (
    mock_client,
    mock_config_entry,
    mock_setup_entry,
    post_connection_delay,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _delay: None = Depends(post_connection_delay),
) -> None:
    """Wire module-level fixtures (post_connection_delay is autouse in pytest)."""


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Ness Alarm 192.168.1.100:1992")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: False,
        }
    )
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)
    client.close.assert_awaited_once()


@test
async def user_flow_with_infer_arming_state(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow with infer_arming_state enabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_INFER_ARMING_STATE]).to_be(True)


@test
async def user_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("os_error", OSError("Connection refused"), "cannot_connect"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("runtime", RuntimeError("Unexpected"), "unknown"),
)
async def user_flow_connection_error_recovery(
    side_effect: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection error handling and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.update.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})
    client.close.assert_awaited_once()

    client.update.side_effect = None
    client.close.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
            CONF_INFER_ARMING_STATE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def import_yaml_config(
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test importing YAML configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_HOST: "192.168.1.72",
            CONF_PORT: 4999,
            CONF_INFER_ARMING_STATE: False,
            CONF_ZONES: [
                {CONF_ZONE_NAME: "Garage", CONF_ZONE_ID: 1},
                {
                    CONF_ZONE_NAME: "Front Door",
                    CONF_ZONE_ID: 5,
                    CONF_ZONE_TYPE: BinarySensorDeviceClass.DOOR,
                },
            ],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Ness Alarm 192.168.1.72:4999")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.72",
            CONF_PORT: 4999,
            CONF_INFER_ARMING_STATE: False,
        }
    )

    expect(len(result["subentries"])).to_equal(2)
    expect(result["subentries"][0]["title"]).to_equal("Zone 1")
    expect(result["subentries"][0]["unique_id"]).to_equal("zone_1")
    expect(result["subentries"][0]["data"][CONF_TYPE]).to_equal(
        BinarySensorDeviceClass.MOTION
    )
    expect(result["subentries"][0]["data"][CONF_ZONE_NAME]).to_equal("Garage")
    expect(result["subentries"][1]["title"]).to_equal("Zone 5")
    expect(result["subentries"][1]["unique_id"]).to_equal("zone_5")
    expect(result["subentries"][1]["data"][CONF_TYPE]).to_equal(
        BinarySensorDeviceClass.DOOR
    )
    expect(result["subentries"][1]["data"][CONF_ZONE_NAME]).to_equal("Front Door")

    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)
    client.close.assert_awaited_once()


@test.cases(
    test.case("os_error", OSError("Connection refused"), "cannot_connect"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("runtime", RuntimeError("Unexpected"), "unknown"),
)
async def import_yaml_config_errors(
    side_effect: type[Exception] | Exception,
    expected_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test importing YAML configuration error paths."""
    client.update.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_HOST: "192.168.1.72",
            CONF_PORT: 4999,
            CONF_INFER_ARMING_STATE: False,
            CONF_ZONES: [
                {CONF_ZONE_NAME: "Garage", CONF_ZONE_ID: 1},
                {
                    CONF_ZONE_NAME: "Front Door",
                    CONF_ZONE_ID: 5,
                    CONF_ZONE_TYPE: BinarySensorDeviceClass.DOOR,
                },
            ],
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def import_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort import if already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 4999,
            CONF_ZONES: [],
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("os_error", OSError("Connection refused"), "cannot_connect"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("runtime", RuntimeError("Unexpected"), "unknown"),
)
async def import_connection_errors(
    side_effect: type[Exception] | Exception,
    expected_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test import aborts on connection errors."""
    client.update.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_HOST: "192.168.1.72",
            CONF_PORT: 4999,
            CONF_ZONES: [],
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)
    client.close.assert_awaited_once()


@test
async def zone_subentry_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test adding a zone through subentry flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ZONE),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_ZONE_NUMBER: 1,
            CONF_TYPE: BinarySensorDeviceClass.DOOR,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Zone 1")
    expect(result["data"][CONF_ZONE_NUMBER]).to_equal(1)
    expect(result["data"][CONF_TYPE]).to_equal(BinarySensorDeviceClass.DOOR)


@test
async def zone_subentry_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test adding a zone that already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )
    entry.add_to_hass(hass)

    entry.subentries = {
        "zone_1_id": ConfigSubentry(
            subentry_type=SUBENTRY_TYPE_ZONE,
            subentry_id="zone_1_id",
            unique_id="zone_1",
            title="Zone 1",
            data=MappingProxyType(
                {
                    CONF_ZONE_NUMBER: 1,
                    CONF_TYPE: BinarySensorDeviceClass.MOTION,
                }
            ),
        )
    }

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ZONE),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_ZONE_NUMBER: 1,
            CONF_TYPE: BinarySensorDeviceClass.DOOR,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ZONE_NUMBER: "already_configured"})


@test
async def zone_subentry_reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring an existing zone."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )
    entry.add_to_hass(hass)

    zone_subentry = ConfigSubentry(
        subentry_type=SUBENTRY_TYPE_ZONE,
        subentry_id="zone_1_id",
        unique_id="zone_1",
        title="Zone 1",
        data=MappingProxyType(
            {
                CONF_ZONE_NUMBER: 1,
                CONF_TYPE: BinarySensorDeviceClass.MOTION,
            }
        ),
    )
    entry.subentries = {"zone_1_id": zone_subentry}

    result = await entry.start_subentry_reconfigure_flow(hass, "zone_1_id")

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["description_placeholders"][CONF_ZONE_NUMBER]).to_equal("1")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_TYPE: BinarySensorDeviceClass.DOOR,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow to configure alarm panel settings."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SHOW_HOME_MODE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_SHOW_HOME_MODE]).to_be(False)


@test
async def options_flow_enable_home_mode(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to enable home mode."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
        options={CONF_SHOW_HOME_MODE: False},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SHOW_HOME_MODE: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_SHOW_HOME_MODE]).to_be(True)
