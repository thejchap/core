"""Tests for Comelit SimpleHome config flow."""

from unittest.mock import AsyncMock

from aiocomelit import CannotAuthenticate, CannotConnect
from aiocomelit.const import BRIDGE, VEDO
from tryke import Depends, expect, fixture, test

from homeassistant.components.comelit.config_flow import (
    InvalidPin,
    InvalidVedoAuth,
    InvalidVedoPin,
)
from homeassistant.components.comelit.const import CONF_VEDO_PIN, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PIN, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_serial_bridge,
    mock_serial_bridge_config_entry,
    mock_vedo,
    mock_vedo_config_entry,
)
from .const import (
    BAD_PIN,
    BRIDGE_HOST,
    BRIDGE_PIN,
    BRIDGE_PORT,
    BRIDGE_VEDO_PIN,
    FAKE_PIN,
    VEDO_HOST,
    VEDO_PIN,
    VEDO_PORT,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def flow_serial_bridge(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bridge: AsyncMock = Depends(mock_serial_bridge),
    _entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_TYPE: BRIDGE,
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)
    await hass.async_block_till_done()


@test
async def flow_vedo(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _vedo: AsyncMock = Depends(mock_vedo),
    _entry: MockConfigEntry = Depends(mock_vedo_config_entry),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)
    await hass.async_block_till_done()


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
    test.case("invalid_pin", side_effect=InvalidPin, error="invalid_pin"),
    test.case("invalid_vedo_pin", side_effect=InvalidVedoPin, error="invalid_vedo_pin"),
    test.case(
        "invalid_vedo_auth", side_effect=InvalidVedoAuth, error="invalid_vedo_auth"
    ),
)
async def exception_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vedo: AsyncMock = Depends(mock_vedo),
    _entry: MockConfigEntry = Depends(mock_vedo_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test starting a flow by user with a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    vedo.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    vedo.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(VEDO_HOST)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: VEDO_HOST,
            CONF_PORT: VEDO_PORT,
            CONF_PIN: VEDO_PIN,
            CONF_TYPE: VEDO,
        }
    )


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _vedo: AsyncMock = Depends(mock_vedo),
    entry: MockConfigEntry = Depends(mock_vedo_config_entry),
) -> None:
    """Test starting a reauthentication flow."""
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: FAKE_PIN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
    test.case("invalid_pin", side_effect=InvalidPin, error="invalid_pin"),
)
async def reauth_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vedo: AsyncMock = Depends(mock_vedo),
    entry: MockConfigEntry = Depends(mock_vedo_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    vedo.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: FAKE_PIN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    vedo.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: VEDO_PIN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PIN]).to_equal(VEDO_PIN)


@test
async def reconfigure_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bridge: AsyncMock = Depends(mock_serial_bridge),
    entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test that the host can be reconfigured."""
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    expect(entry.data[CONF_HOST]).to_equal("fake_bridge_host")

    new_host = "new_bridge_host"

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: new_host,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BRIDGE_VEDO_PIN,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    expect(entry.data[CONF_HOST]).to_equal(new_host)


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
    test.case("invalid_pin", side_effect=InvalidPin, error="invalid_pin"),
    test.case("invalid_vedo_pin", side_effect=InvalidVedoPin, error="invalid_vedo_pin"),
    test.case(
        "invalid_vedo_auth", side_effect=InvalidVedoAuth, error="invalid_vedo_auth"
    ),
)
async def reconfigure_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bridge: AsyncMock = Depends(mock_serial_bridge),
    entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test that the host can be reconfigured."""
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    bridge.login.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.60",
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")
    expect(reconfigure_result["errors"]).to_equal({"base": error})

    bridge.login.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.61",
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_HOST: "192.168.100.61",
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_TYPE: BRIDGE,
        }
    )


@test
async def pin_format_serial_bridge(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bridge: AsyncMock = Depends(mock_serial_bridge),
    _entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test PIN is valid format."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BAD_PIN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_pin"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_TYPE: BRIDGE,
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)
    await hass.async_block_till_done()


@test
async def flow_serial_bridge_with_vedo_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bridge: AsyncMock = Depends(mock_serial_bridge),
    _entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test starting a flow by user with VEDO PIN."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    bridge.vedo_enabled.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BRIDGE_VEDO_PIN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BRIDGE_VEDO_PIN,
            CONF_TYPE: BRIDGE,
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)
    await hass.async_block_till_done()


@test
async def flow_serial_bridge_with_invalid_vedo_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bridge: AsyncMock = Depends(mock_serial_bridge),
    _entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test starting a flow with invalid VEDO PIN."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BAD_PIN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_vedo_pin"})

    bridge.vedo_enabled.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BRIDGE_VEDO_PIN,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_serial_bridge_with_vedo_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bridge: AsyncMock = Depends(mock_serial_bridge),
    _entry: MockConfigEntry = Depends(mock_serial_bridge_config_entry),
) -> None:
    """Test starting a flow with VEDO authentication failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    bridge.vedo_enabled.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
            CONF_VEDO_PIN: BRIDGE_VEDO_PIN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_vedo_auth"})
