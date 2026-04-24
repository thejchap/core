"""Test the Prosegur Alarm config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.prosegur.config_flow import CannotConnect, InvalidAuth
from homeassistant.components.prosegur.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_list_contracts as mock_list_contracts_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_list_contracts: list[dict[str, str]] = Depends(mock_list_contracts_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.prosegur.config_flow.Installation.list",
            return_value=mock_list_contracts,
        ) as mock_retrieve,
        patch(
            "homeassistant.components.prosegur.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country": "PT",
            },
        )
        await hass.async_block_till_done()

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"contract": "123"},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Contract 123")
    expect(result3["data"]).to_equal(
        {
            "contract": "123",
            "username": "test-username",
            "password": "test-password",
            "country": "PT",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_retrieve.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pyprosegur.installation.Installation.list",
        side_effect=ConnectionRefusedError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country": "PT",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.prosegur.config_flow.Installation.list",
        side_effect=ConnectionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country": "PT",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.prosegur.config_flow.Installation.list",
        side_effect=ValueError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country": "PT",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_list_contracts: list[dict[str, str]] = Depends(mock_list_contracts_fx),
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            "username": "test-username",
            "password": "test-password",
            "country": "PT",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.prosegur.config_flow.Installation.list",
            return_value=mock_list_contracts,
        ) as mock_installation,
        patch(
            "homeassistant.components.prosegur.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new_password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            "country": "PT",
            "username": "test-username",
            "password": "new_password",
        }
    )
    expect(len(mock_installation.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("cannot_connect", exception=CannotConnect, base_error="cannot_connect"),
    test.case("invalid_auth", exception=InvalidAuth, base_error="invalid_auth"),
    test.case("unknown", exception=Exception, base_error="unknown"),
)
async def reauth_flow_error(
    exception: type[Exception],
    base_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a reauthentication flow with errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            "username": "test-username",
            "password": "test-password",
            "country": "PT",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.prosegur.config_flow.Installation.list",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new_password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal(base_error)
