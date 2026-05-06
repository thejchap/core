"""Tests for the Pinecil config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pynecil import CommunicationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.iron_os import DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    DEFAULT_NAME,
    PINECIL_SERVICE_INFO,
    USER_INPUT,
    config_entry,
    config_entry_ignored,
    discovery,
    mock_ironosupdate,
    mock_pynecil,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
    _ironos: AsyncMock = Depends(mock_ironosupdate),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def async_step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: MagicMock = Depends(discovery),
    _pynecil: AsyncMock = Depends(mock_pynecil),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("c0:ff:ee:c0:ff:ee")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "communication_error",
        raise_error=CommunicationError,
        text_error="cannot_connect",
    ),
    test.case("unknown", raise_error=Exception, text_error="unknown"),
)
async def async_step_user_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: MagicMock = Depends(discovery),
    pynecil: AsyncMock = Depends(mock_pynecil),
    *,
    raise_error: type[Exception],
    text_error: str,
) -> None:
    """Test the user config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    pynecil.connect.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    pynecil.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("c0:ff:ee:c0:ff:ee")


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: MagicMock = Depends(discovery),
    _pynecil: AsyncMock = Depends(mock_pynecil),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test the device gets added via another flow between steps."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_no_device_discovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    discovery_mock: MagicMock = Depends(discovery),
) -> None:
    """Test setup with no device discoveries."""
    discovery_mock.return_value = []
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_bluetooth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pynecil: AsyncMock = Depends(mock_pynecil),
) -> None:
    """Test discovery via bluetooth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=PINECIL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("c0:ff:ee:c0:ff:ee")


@test.cases(
    test.case(
        "communication_error",
        raise_error=CommunicationError,
        text_error="cannot_connect",
    ),
    test.case("unknown", raise_error=Exception, text_error="unknown"),
)
async def async_step_bluetooth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pynecil: AsyncMock = Depends(mock_pynecil),
    *,
    raise_error: type[Exception],
    text_error: str,
) -> None:
    """Test discovery via bluetooth errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=PINECIL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    pynecil.connect.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    pynecil.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("c0:ff:ee:c0:ff:ee")


@test
async def async_step_bluetooth_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pynecil: AsyncMock = Depends(mock_pynecil),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we can't start a flow if there is already a config entry."""

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=PINECIL_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _discovery: MagicMock = Depends(discovery),
    _pynecil: AsyncMock = Depends(mock_pynecil),
    entry_ignored: MockConfigEntry = Depends(config_entry_ignored),
) -> None:
    """Test the user initiated form can replace an ignored device."""

    entry_ignored.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("c0:ff:ee:c0:ff:ee")
