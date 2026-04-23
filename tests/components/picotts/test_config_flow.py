"""Test the Pico TTS config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import tts
from homeassistant.components.picotts.const import DOMAIN
from homeassistant.components.tts import CONF_LANG
from homeassistant.const import CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fx,
    mock_network,
)

from ._fixtures import mock_setup_entry as mock_setup_entry_fx


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network and mock_setup_entry for every test."""


@test
async def user_step(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test user step create entry result."""
    with patch(
        "homeassistant.components.picotts.shutil.which",
        return_value="/usr/local/bin/pico2wave",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_be(None)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANG: "es-ES",
            },
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Pico TTS es-ES")
        expect(result["data"]).to_equal({CONF_LANG: "es-ES"})
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_step_binary_not_found(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step aborts when binary not found."""
    with patch(
        "homeassistant.components.picotts.shutil.which",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("binary_not_found")


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test user step already configured entry."""
    with patch(
        "homeassistant.components.picotts.shutil.which",
        return_value="/usr/local/bin/pico2wave",
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_LANG: "es-ES"})
        config_entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_be(None)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANG: "es-ES",
            },
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
        expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def import_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test the import flow."""
    with patch(
        "homeassistant.components.picotts.shutil.which",
        return_value="/usr/local/bin/pico2wave",
    ):
        expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
        expect(
            bool(
                await async_setup_component(
                    hass,
                    tts.DOMAIN,
                    {tts.DOMAIN: {CONF_PLATFORM: DOMAIN}},
                )
            )
        ).to_be(True)
        await hass.async_block_till_done()
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        config_entry = hass.config_entries.async_entries(DOMAIN)[0]
        expect(config_entry.state).to_be(config_entries.ConfigEntryState.LOADED)
        expect(
            bool(
                issue_registry.async_get_issue(
                    domain=DOMAIN,
                    issue_id=f"deprecated_yaml_{DOMAIN}",
                )
            )
        ).to_be(True)
