"""Test the Sense config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from sense_energy import (
    SenseAPIException,
    SenseAPITimeoutException,
    SenseAuthenticationException,
    SenseMFARequiredException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sense.const import DOMAIN
from homeassistant.const import CONF_CODE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_sense
from .const import MOCK_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.sense.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-email")
    expect(result2["data"]).to_equal(MOCK_CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=SenseAuthenticationException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_mfa_required(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    sense.return_value.authenticate.side_effect = SenseMFARequiredException

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"timeout": "6", "email": "test-email", "password": "test-password"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("validation")

    sense.return_value.validate_mfa.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CODE: "012345"},
    )

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("test-email")
    expect(result3["data"]).to_equal(MOCK_CONFIG)


@test
async def form_mfa_required_wrong(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    sense.return_value.authenticate.side_effect = SenseMFARequiredException

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"timeout": "6", "email": "test-email", "password": "test-password"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("validation")

    sense.return_value.validate_mfa.side_effect = SenseAuthenticationException
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CODE: "000000"},
    )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "invalid_auth"})
    expect(result3["step_id"]).to_equal("validation")


@test
async def form_mfa_required_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    sense.return_value.authenticate.side_effect = SenseMFARequiredException

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"timeout": "6", "email": "test-email", "password": "test-password"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("validation")

    sense.return_value.validate_mfa.side_effect = SenseAPITimeoutException
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CODE: "000000"},
    )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_mfa_required_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    sense.return_value.authenticate.side_effect = SenseMFARequiredException

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"timeout": "6", "email": "test-email", "password": "test-password"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("validation")

    sense.return_value.validate_mfa.side_effect = Exception
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CODE: "000000"},
    )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "unknown"})


@test
async def form_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=SenseAPITimeoutException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=SenseAPIException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth_no_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test reauth where no form needed."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="test-email",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload",
        return_value=True,
    ):
        result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sense: AsyncMock = Depends(mock_sense),
) -> None:
    """Test reauth form."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="test-email",
    )
    entry.add_to_hass(hass)
    sense.return_value.authenticate.side_effect = SenseAuthenticationException

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    sense.return_value.authenticate.side_effect = None
    with patch(
        "homeassistant.components.sense.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
