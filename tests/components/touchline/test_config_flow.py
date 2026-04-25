"""Test the Touchline config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.touchline.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_pytouchline, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_HOST = "1.2.3.4"
TEST_DATA = {CONF_HOST: TEST_HOST}
TEST_UNIQUE_ID = "controller-1"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pytouchline: MagicMock = Depends(mock_pytouchline),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_HOST)
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal(TEST_UNIQUE_ID)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pytouchline: MagicMock = Depends(mock_pytouchline),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    # The config flow runs validation in a thread executor.
    # If `get_number_of_devices` fails, validation fails too.
    pytouchline.get_number_of_devices.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    # "Fix" the problem, and try again.
    pytouchline.get_number_of_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_HOST)
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal(TEST_UNIQUE_ID)


@test
async def already_configured_by_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pytouchline: MagicMock = Depends(mock_pytouchline),
) -> None:
    """Test abort when host is already configured."""
    MockConfigEntry(domain=DOMAIN, data=TEST_DATA).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def already_configured_by_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pytouchline: MagicMock = Depends(mock_pytouchline),
) -> None:
    """Test abort when unique id is already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "5.6.7.8"},
        unique_id=TEST_UNIQUE_ID,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def import_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pytouchline: MagicMock = Depends(mock_pytouchline),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test YAML import creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_HOST)
    expect(result["data"]).to_equal(TEST_DATA)
    expect(result["result"].unique_id).to_equal(TEST_UNIQUE_ID)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def import_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pytouchline: MagicMock = Depends(mock_pytouchline),
) -> None:
    """Test YAML import aborts when it cannot connect."""
    pytouchline.get_number_of_devices.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def import_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pytouchline: MagicMock = Depends(mock_pytouchline),
) -> None:
    """Test YAML import aborts when already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "5.6.7.8"},
        unique_id=TEST_UNIQUE_ID,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=TEST_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
