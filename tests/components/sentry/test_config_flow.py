"""Test the sentry config flow."""

from __future__ import annotations

import logging
from unittest.mock import patch

from sentry_sdk.utils import BadDsn
from tryke import Depends, expect, fixture, test

from homeassistant.components.sentry.const import (
    CONF_ENVIRONMENT,
    CONF_EVENT_CUSTOM_COMPONENTS,
    CONF_EVENT_HANDLED,
    CONF_EVENT_THIRD_PARTY_PACKAGES,
    CONF_LOGGING_EVENT_LEVEL,
    CONF_LOGGING_LEVEL,
    CONF_TRACING,
    CONF_TRACING_SAMPLE_RATE,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    with (
        patch("homeassistant.components.sentry.config_flow.Dsn"),
        patch(
            "homeassistant.components.sentry.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "http://public@sentry.local/1"},
        )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Sentry")
    expect(result2.get("data")).to_equal({"dsn": "http://public@sentry.local/1"})
    await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def integration_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def user_flow_bad_dsn(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle bad dsn error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.sentry.config_flow.Dsn",
        side_effect=BadDsn,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "foo"},
        )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "bad_dsn"})


@test
async def user_flow_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle any unknown exception error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.sentry.config_flow.Dsn",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "foo"},
        )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "unknown"})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"dsn": "http://public@sentry.local/1"},
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.sentry.async_setup_entry", return_value=True):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENVIRONMENT: "Test",
            CONF_EVENT_CUSTOM_COMPONENTS: True,
            CONF_EVENT_HANDLED: True,
            CONF_EVENT_THIRD_PARTY_PACKAGES: True,
            CONF_LOGGING_EVENT_LEVEL: logging.DEBUG,
            CONF_LOGGING_LEVEL: logging.DEBUG,
            CONF_TRACING: True,
            CONF_TRACING_SAMPLE_RATE: 0.5,
        },
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal(
        {
            CONF_ENVIRONMENT: "Test",
            CONF_EVENT_CUSTOM_COMPONENTS: True,
            CONF_EVENT_HANDLED: True,
            CONF_EVENT_THIRD_PARTY_PACKAGES: True,
            CONF_LOGGING_EVENT_LEVEL: logging.DEBUG,
            CONF_LOGGING_LEVEL: logging.DEBUG,
            CONF_TRACING: True,
            CONF_TRACING_SAMPLE_RATE: 0.5,
        }
    )
