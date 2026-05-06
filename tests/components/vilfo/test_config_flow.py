"""Test the Vilfo Router config flow."""

from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from vilfo.exceptions import AuthenticationException, VilfoException

from homeassistant.components.vilfo.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_is_valid_host,
    mock_setup_entry,
    mock_vilfo_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "domain_no_mac",
        user_input={CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
        expected_unique_id="testadmin.vilfo.com",
        mac=None,
    ),
    test.case(
        "domain_with_mac",
        user_input={CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
        expected_unique_id="FF-00-00-00-00-00",
        mac="FF-00-00-00-00-00",
    ),
    test.case(
        "ipv4",
        user_input={CONF_HOST: "192.168.0.1", CONF_ACCESS_TOKEN: "test-token"},
        expected_unique_id="FF-00-00-00-00-00",
        mac="FF-00-00-00-00-00",
    ),
    test.case(
        "ipv6",
        user_input={CONF_HOST: "2001:db8::1428:57ab", CONF_ACCESS_TOKEN: "test-token"},
        expected_unique_id="FF-00-00-00-00-00",
        mac="FF-00-00-00-00-00",
    ),
)
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vilfo_client: AsyncMock = Depends(mock_vilfo_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _is_valid_host: AsyncMock = Depends(mock_is_valid_host),
    *,
    user_input: dict[str, Any],
    expected_unique_id: str,
    mac: str | None,
) -> None:
    """Test we can finish a config flow."""
    vilfo_client.resolve_mac_address.return_value = mac
    vilfo_client.mac = mac

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(user_input[CONF_HOST])
    expect(result["data"]).to_equal(user_input)
    expect(result["result"].unique_id).to_equal(expected_unique_id)

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vilfo_client: AsyncMock = Depends(mock_vilfo_client),
    _is_valid_host: AsyncMock = Depends(mock_is_valid_host),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid auth."""
    vilfo_client.get_board_information.side_effect = AuthenticationException
    vilfo_client.resolve_mac_address.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    vilfo_client.get_board_information.side_effect = None
    vilfo_client.resolve_mac_address.return_value = "FF-00-00-00-00-00"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("cannot_connect", side_effect=VilfoException, error="cannot_connect"),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def form_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vilfo_client: AsyncMock = Depends(mock_vilfo_client),
    _is_valid_host: AsyncMock = Depends(mock_is_valid_host),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test we handle exceptions."""
    vilfo_client.ping.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    vilfo_client.ping.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_wrong_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    is_valid_host: AsyncMock = Depends(mock_is_valid_host),
) -> None:
    """Test we handle wrong host errors."""
    is_valid_host.return_value = False
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "this is an invalid hostname",
            CONF_ACCESS_TOKEN: "test-token",
        },
    )

    expect(result["errors"]).to_equal({"base": "invalid_host"})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _vilfo_client: AsyncMock = Depends(mock_vilfo_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _is_valid_host: AsyncMock = Depends(mock_is_valid_host),
) -> None:
    """Test that we handle already configured exceptions appropriately."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "testadmin.vilfo.com", CONF_ACCESS_TOKEN: "test-token"},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
