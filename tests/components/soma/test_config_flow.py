"""Tests for the Soma config flow."""

from __future__ import annotations

from unittest.mock import patch

from api.soma_api import SomaApi
from requests import RequestException
from tryke import Depends, expect, fixture, test

from homeassistant.components.soma import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_HOST = "123.45.67.89"
MOCK_PORT = 3000


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user form showing."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def import_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration from YAML aborting with existing entity."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_setup")


@test
async def import_create(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration from YAML."""
    with patch.object(SomaApi, "list_devices", return_value={"result": "success"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={"host": MOCK_HOST, "port": MOCK_PORT},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def error_status(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Connect successfully returning error status."""
    with patch.object(SomaApi, "list_devices", return_value={"result": "error"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={"host": MOCK_HOST, "port": MOCK_PORT},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("result_error")


@test
async def key_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Connect returning empty string."""
    with patch.object(SomaApi, "list_devices", return_value={}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={"host": MOCK_HOST, "port": MOCK_PORT},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("connection_error")


@test
async def exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if RequestException fires when no connection can be made."""
    with patch.object(SomaApi, "list_devices", side_effect=RequestException()):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={"host": MOCK_HOST, "port": MOCK_PORT},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("connection_error")


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check classic use case."""
    hass.data[DOMAIN] = {}
    with patch.object(SomaApi, "list_devices", return_value={"result": "success"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"host": MOCK_HOST, "port": MOCK_PORT},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
