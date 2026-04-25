"""Tests for the LCN config flow."""

from unittest.mock import patch

from pypck.connection import (
    PchkAuthenticationError,
    PchkConnectionFailedError,
    PchkConnectionRefusedError,
    PchkLicenseError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.lcn.config_flow import LcnFlowHandler, validate_connection
from homeassistant.components.lcn.const import (
    CONF_ACKNOWLEDGE,
    CONF_DIM_MODE,
    CONF_SK_NUM_TRIES,
    DOMAIN,
)
from homeassistant.const import (
    CONF_BASE,
    CONF_DEVICES,
    CONF_ENTITIES,
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from ._fixtures import entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG_DATA = {
    CONF_IP_ADDRESS: "127.0.0.1",
    CONF_PORT: 1234,
    CONF_USERNAME: "lcn",
    CONF_PASSWORD: "lcn",
    CONF_SK_NUM_TRIES: 0,
    CONF_DIM_MODE: "STEPS200",
    CONF_ACKNOWLEDGE: False,
}

CONNECTION_DATA = {CONF_HOST: "pchk", **CONFIG_DATA}

IMPORT_DATA = {
    **CONNECTION_DATA,
    CONF_DEVICES: [],
    CONF_ENTITIES: [],
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the form is served with no input."""
    flow = LcnFlowHandler()
    flow.hass = hass

    result = await flow.async_step_user(user_input=None)

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for user step."""
    with (
        patch("homeassistant.components.lcn.PchkConnectionManager.async_connect"),
        patch("homeassistant.components.lcn.async_setup_entry", return_value=True),
    ):
        data = CONNECTION_DATA.copy()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(CONNECTION_DATA[CONF_HOST])
        expect(result["data"]).to_equal(
            {
                **CONNECTION_DATA,
                CONF_DEVICES: [],
                CONF_ENTITIES: [],
            }
        )


@test
async def step_user_existing_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(entry),
) -> None:
    """Test for user defined host already exists."""
    config_entry.add_to_hass(hass)

    with patch("homeassistant.components.lcn.PchkConnectionManager.async_connect"):
        config_data = config_entry.data.copy()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=config_data
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "auth_error",
        error=PchkAuthenticationError,
        errors={CONF_BASE: "authentication_error"},
    ),
    test.case(
        "license_error",
        error=PchkLicenseError,
        errors={CONF_BASE: "license_error"},
    ),
    test.case(
        "connection_failed",
        error=PchkConnectionFailedError,
        errors={CONF_BASE: "connection_refused"},
    ),
    test.case(
        "connection_refused",
        error=PchkConnectionRefusedError,
        errors={CONF_BASE: "connection_refused"},
    ),
)
async def step_user_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: type[Exception],
    errors: dict[str, str],
) -> None:
    """Test for error in user step is handled correctly."""
    with patch(
        "homeassistant.components.lcn.PchkConnectionManager.async_connect",
        side_effect=error,
    ):
        data = CONNECTION_DATA.copy()
        data.update({CONF_HOST: "pchk"})
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["errors"]).to_equal(errors)


@test
async def step_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(entry),
) -> None:
    """Test for reconfigure step."""
    config_entry.add_to_hass(hass)
    old_entry_data = config_entry.data.copy()

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with (
        patch("homeassistant.components.lcn.PchkConnectionManager.async_connect"),
        patch("homeassistant.components.lcn.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG_DATA.copy(),
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reconfigure_successful")

        updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
        expect(updated_entry.title).to_equal(CONNECTION_DATA[CONF_HOST])
        expect(updated_entry.data).to_equal({**old_entry_data, **CONFIG_DATA})


@test.cases(
    test.case(
        "auth_error",
        error=PchkAuthenticationError,
        errors={CONF_BASE: "authentication_error"},
    ),
    test.case(
        "license_error",
        error=PchkLicenseError,
        errors={CONF_BASE: "license_error"},
    ),
    test.case(
        "connection_failed",
        error=PchkConnectionFailedError,
        errors={CONF_BASE: "connection_refused"},
    ),
    test.case(
        "connection_refused",
        error=PchkConnectionRefusedError,
        errors={CONF_BASE: "connection_refused"},
    ),
)
async def step_reconfigure_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(entry),
    *,
    error: type[Exception],
    errors: dict[str, str],
) -> None:
    """Test for error in reconfigure step is handled correctly."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.lcn.PchkConnectionManager.async_connect",
        side_effect=error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG_DATA.copy(),
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["errors"]).to_equal(errors)


@test
async def validate_connection_test(
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test the connection validation."""
    data = CONNECTION_DATA.copy()

    with (
        patch(
            "homeassistant.components.lcn.PchkConnectionManager.async_connect"
        ) as async_connect,
        patch(
            "homeassistant.components.lcn.PchkConnectionManager.async_close"
        ) as async_close,
    ):
        result = await validate_connection(data=data)

    expect(bool(async_connect.is_called)).to_be(True)
    expect(bool(async_close.is_called)).to_be(True)
    expect(result).to_be(None)
