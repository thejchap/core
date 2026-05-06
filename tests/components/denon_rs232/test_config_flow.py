"""Tests for the Denon RS232 config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.denon_rs232.config_flow import CONF_MODEL_NAME
from homeassistant.components.denon_rs232.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_DEVICE, MOCK_MODEL, MOCK_MODEL_SELECTION
from ._fixtures import MockReceiver, mock_receiver, mock_usb_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _usb: None = Depends(mock_usb_component),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@fixture
def mock_async_setup_entry() -> AsyncMock:
    """Prevent config-entry creation tests from setting up the integration."""
    with patch(
        "homeassistant.components.denon_rs232.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@test
async def user_form_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    receiver: MockReceiver = Depends(mock_receiver),
    setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test successful config flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.denon_rs232.config_flow.DenonReceiver",
        return_value=receiver,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: MOCK_DEVICE, CONF_MODEL: MOCK_MODEL_SELECTION},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("AVR-3805")
    expect(result["data"]).to_equal(
        {
            CONF_DEVICE: MOCK_DEVICE,
            CONF_MODEL: MOCK_MODEL,
            CONF_MODEL_NAME: "AVR-3805",
        }
    )
    setup_entry.assert_awaited_once()
    receiver.connect.assert_awaited_once()
    receiver.disconnect.assert_awaited_once()


@test.cases(
    test.case(
        "value_error",
        exception=ValueError("Invalid port"),
        error="cannot_connect",
    ),
    test.case(
        "connection_error",
        exception=ConnectionError("No response"),
        error="cannot_connect",
    ),
    test.case(
        "os_error", exception=OSError("No such device"), error="cannot_connect"
    ),
    test.case("runtime_error", exception=RuntimeError("boom"), error="unknown"),
)
async def user_form_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    receiver: MockReceiver = Depends(mock_receiver),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test the user step reports connection and unexpected errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    receiver.connect.side_effect = exception

    with patch(
        "homeassistant.components.denon_rs232.config_flow.DenonReceiver",
        return_value=receiver,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: MOCK_DEVICE, CONF_MODEL: MOCK_MODEL_SELECTION},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    receiver.connect.side_effect = None

    with patch(
        "homeassistant.components.denon_rs232.config_flow.DenonReceiver",
        return_value=receiver,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: MOCK_DEVICE, CONF_MODEL: MOCK_MODEL_SELECTION},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_duplicate_port_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if the same port is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: MOCK_DEVICE, CONF_MODEL: MOCK_MODEL},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DEVICE: MOCK_DEVICE, CONF_MODEL: MOCK_MODEL_SELECTION},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
