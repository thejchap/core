"""Define tests for the The Things Network init."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from ttn_client import TTNAuthError

from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_ttnclient

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test.cases(
    test.case("ttn_auth_error", exception_class=TTNAuthError),
    test.case("generic_exception", exception_class=Exception),
)
async def init_exceptions(
    *,
    exception_class: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ttnclient: MagicMock = Depends(mock_ttnclient),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test TTN Exceptions."""
    ttnclient.return_value.fetch_data.side_effect = exception_class
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(False)
