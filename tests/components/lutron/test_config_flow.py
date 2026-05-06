"""Test the lutron config flow."""

from email.message import Message
from unittest.mock import AsyncMock, patch
from urllib.error import HTTPError

from tryke import Depends, expect, fixture, test

from homeassistant.components.lutron.const import CONF_DEFAULT_DIMMER_LEVEL, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_DATA_STEP = {
    CONF_HOST: "127.0.0.1",
    CONF_USERNAME: "lutron",
    CONF_PASSWORD: "integration",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test success response."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch("homeassistant.components.lutron.config_flow.Lutron.load_xml_db"),
        patch("homeassistant.components.lutron.config_flow.Lutron.guid", "12345678901"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].title).to_equal("Lutron")

        expect(result["data"]).to_equal(MOCK_DATA_STEP)


@test.cases(
    test.case(
        "http_error",
        raise_error=HTTPError("", 404, "", Message(), None),
        text_error="cannot_connect",
    ),
    test.case("unknown_exception", raise_error=Exception, text_error="unknown"),
)
async def flow_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    raise_error: object,
    text_error: str,
) -> None:
    """Test unknown errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.lutron.config_flow.Lutron.load_xml_db",
        side_effect=raise_error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    with (
        patch("homeassistant.components.lutron.config_flow.Lutron.load_xml_db"),
        patch("homeassistant.components.lutron.config_flow.Lutron.guid", "12345678901"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["result"].title).to_equal("Lutron")

        expect(result["data"]).to_equal(MOCK_DATA_STEP)


@test
async def flow_incorrect_guid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test configuring flow with incorrect guid."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch("homeassistant.components.lutron.config_flow.Lutron.load_xml_db"),
        patch("homeassistant.components.lutron.config_flow.Lutron.guid", "12345"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch("homeassistant.components.lutron.config_flow.Lutron.load_xml_db"),
        patch("homeassistant.components.lutron.config_flow.Lutron.guid", "12345678901"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_single_instance_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort user data set when entry is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_DATA_STEP, unique_id="12345678901"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA_STEP,
        unique_id="12345678901",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    # Try to set an out of range dimmer level (260) — voluptuous validation
    # raises before the handler processes it.
    out_of_range_level = 260
    raised = False
    try:
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_DEFAULT_DIMMER_LEVEL: out_of_range_level},
        )
    except InvalidData:
        raised = True
    expect(raised).to_be(True)

    # Now try with a valid value.
    valid_level = 100

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_DEFAULT_DIMMER_LEVEL: valid_level},
    )

    # Verify that the flow finishes successfully with the valid value.
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_DEFAULT_DIMMER_LEVEL: valid_level})
