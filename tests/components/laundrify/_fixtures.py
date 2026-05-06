"""Tryke fixtures for the laundrify integration."""

import json
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from laundrify_aio import LaundrifyAPI, LaundrifyDevice
from tryke import Depends, fixture

from homeassistant.components.laundrify.const import DOMAIN, MANUFACTURER
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant

from .const import VALID_ACCESS_TOKEN, VALID_ACCOUNT_ID

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_device() -> LaundrifyDevice:
    """Return a default Laundrify power sensor mock."""
    machine_data = json.loads(load_fixture("laundrify/machines.json"))[0]

    mock_device = AsyncMock(spec=LaundrifyDevice)
    mock_device.id = machine_data["id"]
    mock_device.manufacturer = MANUFACTURER
    mock_device.model = machine_data["model"]
    mock_device.name = machine_data["name"]
    mock_device.firmwareVersion = machine_data["firmwareVersion"]
    return mock_device


@fixture
def laundrify_api_mock() -> Generator[AsyncMock]:
    """Mock valid laundrify API responses."""
    with (
        patch(
            "laundrify_aio.LaundrifyAPI.get_account_id",
            return_value=1234,
        ),
        patch(
            "laundrify_aio.LaundrifyAPI.validate_token",
            return_value=True,
        ),
        patch(
            "laundrify_aio.LaundrifyAPI.exchange_auth_code",
            return_value=VALID_ACCESS_TOKEN,
        ) as exchange_mock,
        patch(
            "laundrify_aio.LaundrifyAPI.get_machines",
            return_value=[
                LaundrifyDevice(machine, LaundrifyAPI)
                for machine in json.loads(load_fixture("laundrify/machines.json"))
            ],
        ),
    ):
        # Yield the patched LaundrifyAPI class, which exposes the patched
        # methods (e.g. exchange_auth_code) as attributes.
        yield LaundrifyAPI


@fixture
async def laundrify_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(laundrify_api_mock),
) -> MockConfigEntry:
    """Create laundrify entry in Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=VALID_ACCOUNT_ID,
        data={CONF_ACCESS_TOKEN: VALID_ACCESS_TOKEN},
        minor_version=2,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
