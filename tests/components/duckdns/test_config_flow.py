"""Test the Duck DNS config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.duckdns import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    NEW_TOKEN,
    TEST_SUBDOMAIN,
    TEST_TOKEN,
    config_entry,
    mock_setup_entry,
    mock_update_duckdns,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _update: AsyncMock = Depends(mock_update_duckdns),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: "123e4567-e89b-12d3-a456-426614174000",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{TEST_SUBDOMAIN}.duckdns.org")
    expect(result["data"]).to_equal(
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _update: AsyncMock = Depends(mock_update_duckdns),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we abort if already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: "123e4567-e89b-12d3-a456-426614174000",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("unknown", side_effect=[ValueError, True], text_error="unknown"),
    test.case(
        "update_failed", side_effect=[False, True], text_error="update_failed"
    ),
)
async def form_errors(
    side_effect: list[type[Exception] | bool],
    text_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    update_duckdns: AsyncMock = Depends(mock_update_duckdns),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    update_duckdns.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{TEST_SUBDOMAIN}.duckdns.org")
    expect(result["data"]).to_equal(
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def flow_reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _update: AsyncMock = Depends(mock_update_duckdns),
    _setup: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reconfigure flow."""

    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal(NEW_TOKEN)


@test.cases(
    test.case("unknown", side_effect=[ValueError, True], text_error="unknown"),
    test.case(
        "update_failed", side_effect=[False, True], text_error="update_failed"
    ),
)
async def flow_reconfigure_errors(
    side_effect: list[type[Exception] | bool],
    text_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we handle errors."""

    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    update_duckdns.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal(NEW_TOKEN)
