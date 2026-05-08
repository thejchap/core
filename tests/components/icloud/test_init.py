"""Tests for the iCloud config flow."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.icloud.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import MOCK_CONFIG, USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def service_2fa() -> Generator[Mock]:
    """Mock a successful 2fa service."""
    with patch(
        "homeassistant.components.icloud.account.PyiCloudService"
    ) as service_mock:
        service_mock.return_value.requires_2fa = True
        service_mock.return_value.requires_2sa = True
        service_mock.return_value.validate_2fa_code = Mock(return_value=True)
        service_mock.return_value.is_trusted_session = False
        yield service_mock


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def setup_2fa(
    hass: HomeAssistant = Depends(_trigger_executor),
    _service: Mock = Depends(service_2fa),
) -> None:
    """Test that invalid login triggers reauth flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, entry_id="test", unique_id=USERNAME
    )
    config_entry.add_to_hass(hass)

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.config_entries.flow.async_progress())).to_be(False)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    in_progress_flows = hass.config_entries.flow.async_progress()
    expect(len(in_progress_flows)).to_equal(1)
    expect(in_progress_flows[0]["context"]["unique_id"]).to_equal(config_entry.unique_id)
