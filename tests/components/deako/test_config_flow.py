"""Tests for the deako component config flow."""

from unittest.mock import MagicMock

from pydeako.discover import DevicesNotFoundException
from tryke import Depends, expect, fixture, test

from homeassistant.components.deako.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_deako_setup,
    pydeako_deako_mock,
    pydeako_discoverer_mock,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _deako: MagicMock = Depends(pydeako_deako_mock),
    _discoverer: MagicMock = Depends(pydeako_discoverer_mock),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discoverer: MagicMock = Depends(pydeako_discoverer_mock),
    deako_setup: MagicMock = Depends(mock_deako_setup),
) -> None:
    """Test finding a Deako device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Confirmation form.
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    discoverer.return_value.get_address.assert_called_once()

    deako_setup.assert_called_once()


@test
async def not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discoverer: MagicMock = Depends(pydeako_discoverer_mock),
    deako_setup: MagicMock = Depends(mock_deako_setup),
) -> None:
    """Test not finding any Deako devices."""
    discoverer.return_value.get_address.side_effect = DevicesNotFoundException()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Confirmation form.
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
    discoverer.return_value.get_address.assert_called_once()

    deako_setup.assert_not_called()


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    deako_setup: MagicMock = Depends(mock_deako_setup),
) -> None:
    """Test flow aborts when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")

    deako_setup.assert_not_called()
