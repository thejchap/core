"""Test the Schlage config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from pyschlage.exceptions import Error as PyschlageError, NotAuthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.schlage.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MockSchlageConfigEntry
from ._fixtures import (
    mock_added_config_entry,
    mock_pyschlage_auth,
    mock_setup_entry,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("lowercase", username="test-username"),
    test.case("uppercase", username="TEST-USERNAME"),
)
async def form(
    username: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": username,
            "password": "test-password",
        },
    )
    await hass.async_block_till_done()

    pyschlage_auth.authenticate.assert_called_once_with()
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-username")
    expect(result2["data"]).to_equal(
        {
            "username": "test-username",
            "password": "test-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_requires_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    added_entry: MockSchlageConfigEntry = Depends(mock_added_config_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test entries have unique ids."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(init_result["type"]).to_be(FlowResultType.FORM)
    expect(init_result["errors"]).to_equal({})

    create_result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
        },
    )
    await hass.async_block_till_done()

    pyschlage_auth.authenticate.assert_called_once_with()
    expect(create_result["type"]).to_be(FlowResultType.ABORT)
    expect(create_result["reason"]).to_equal("already_configured")


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    pyschlage_auth.authenticate.side_effect = NotAuthorizedError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_unknown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    pyschlage_auth.authenticate.side_effect = PyschlageError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    added_entry: MockSchlageConfigEntry = Depends(mock_added_config_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow."""
    added_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    result = flows[-1]
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"password": "new-password"},
    )
    await hass.async_block_till_done()

    pyschlage_auth.authenticate.assert_called_once_with()
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(added_entry.data).to_equal(
        {
            "username": "asdf@asdf.com",
            "password": "new-password",
        }
    )


@test
async def reauth_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    added_entry: MockSchlageConfigEntry = Depends(mock_added_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
) -> None:
    """Test reauth flow."""
    added_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    [result] = flows
    expect(result["step_id"]).to_equal("reauth_confirm")

    pyschlage_auth.authenticate.reset_mock()
    pyschlage_auth.authenticate.side_effect = NotAuthorizedError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"password": "new-password"},
    )
    await hass.async_block_till_done()

    pyschlage_auth.authenticate.assert_called_once_with()
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    added_entry: MockSchlageConfigEntry = Depends(mock_added_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
) -> None:
    """Test reauth flow."""
    pyschlage_auth.user_id = "bad-user-id"
    added_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    [result] = flows
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"password": "new-password"},
    )
    await hass.async_block_till_done()

    pyschlage_auth.authenticate.assert_called_once_with()
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("wrong_account")
    expect(added_entry.data).to_equal(
        {
            "username": "asdf@asdf.com",
            "password": "hunter2",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
