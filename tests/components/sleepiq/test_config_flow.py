"""Tests for the SleepIQ config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from asyncsleepiq import SleepIQLoginException, SleepIQTimeoutException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.sleepiq.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import SLEEPIQ_CONFIG, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def import_(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we can import a config entry."""
    with patch("asyncsleepiq.AsyncSleepIQ.login"):
        expect(
            await setup.async_setup_component(hass, DOMAIN, {DOMAIN: SLEEPIQ_CONFIG})
        ).to_be(True)
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data[CONF_USERNAME]).to_equal(SLEEPIQ_CONFIG[CONF_USERNAME])
    expect(entry.data[CONF_PASSWORD]).to_equal(SLEEPIQ_CONFIG[CONF_PASSWORD])


@test.cases(
    test.case("login_exc", side_effect=SleepIQLoginException),
    test.case("timeout_exc", side_effect=SleepIQTimeoutException),
)
async def import_failure(
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we won't import a config entry on login failure."""
    with patch(
        "asyncsleepiq.AsyncSleepIQ.login",
        side_effect=side_effect,
    ):
        expect(
            await setup.async_setup_component(hass, DOMAIN, {DOMAIN: SLEEPIQ_CONFIG})
        ).to_be(True)
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)


@test
async def show_set_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    with patch("asyncsleepiq.AsyncSleepIQ.login"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")


@test.cases(
    test.case("login_failure", side_effect=SleepIQLoginException, error="invalid_auth"),
    test.case(
        "timeout_failure", side_effect=SleepIQTimeoutException, error="cannot_connect"
    ),
)
async def login_failure(
    side_effect: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we show user form with appropriate error on login failure."""
    with patch(
        "asyncsleepiq.AsyncSleepIQ.login",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=SLEEPIQ_CONFIG,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": error})


@test
async def success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful flow provides entry creation data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch("asyncsleepiq.AsyncSleepIQ.login", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], SLEEPIQ_CONFIG
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"][CONF_USERNAME]).to_equal(SLEEPIQ_CONFIG[CONF_USERNAME])
    expect(result2["data"][CONF_PASSWORD]).to_equal(SLEEPIQ_CONFIG[CONF_PASSWORD])
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth form."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=SLEEPIQ_CONFIG,
        unique_id=SLEEPIQ_CONFIG[CONF_USERNAME].lower(),
    )
    mock_entry.add_to_hass(hass)
    result = await mock_entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.sleepiq.config_flow.AsyncSleepIQ.login",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
