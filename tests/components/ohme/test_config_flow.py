"""Tests for the Ohme config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ohme import ApiException, AuthException
from tryke import Depends, expect, fixture, test

from homeassistant.components.ohme.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ohme._fixtures import (
    mock_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def config_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_client),
) -> None:
    """Test config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "hunter2"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter2",
        }
    )


@test.cases(
    test.case("invalid_auth", AuthException, "invalid_auth"),
    test.case("unknown", ApiException, "unknown"),
)
async def config_flow_fail(
    test_exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    client.async_login.side_effect = test_exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "hunter1"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "hunter1"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        }
    )


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Ensure we can't add the same account twice."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter3",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_form(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_client),
) -> None:
    """Test reauth form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        },
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter2"},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("invalid_auth", AuthException, "invalid_auth"),
    test.case("unknown", ApiException, "unknown"),
)
async def reauth_fail(
    test_exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test reauth errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    client.async_login.side_effect = test_exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter1"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter2"},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reconfigure_form(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_client),
) -> None:
    """Test reconfigure form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(bool(result["errors"])).to_equal(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter2"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test.cases(
    test.case("invalid_auth", AuthException, "invalid_auth"),
    test.case("unknown", ApiException, "unknown"),
)
async def reconfigure_fail(
    test_exception: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test reconfigure errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )

    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    client.async_login.side_effect = test_exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter1"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter2"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
