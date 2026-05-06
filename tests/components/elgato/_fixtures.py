"""Tryke fixtures for Elgato."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from elgato import BatteryInfo, ElgatoNoBatteryError, Info, Settings, State
from tryke import Depends, fixture

from homeassistant.components.elgato.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC

from tests.common import MockConfigEntry, get_fixture_path, load_fixture
from tests.hass_fixtures import mock_network


@fixture
def device_fixtures() -> str:
    """Return the device fixtures for a specific device."""
    return "key-light"


@fixture
def state_variant() -> str:
    """Return the state variant to load for a device."""
    return "state"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="CN11A1A00001",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        unique_id="CN11A1A00001",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.elgato.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def mock_onboarding() -> Generator[MagicMock]:
    """Mock that Home Assistant is currently onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded",
        return_value=False,
    ) as mock:
        yield mock


@fixture
def mock_elgato(
    device_fixtures: str = Depends(device_fixtures),
    state_variant: str = Depends(state_variant),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> Generator[MagicMock]:
    """Return a mocked Elgato client."""
    with (
        patch(
            "homeassistant.components.elgato.coordinator.Elgato", autospec=True
        ) as elgato_mock,
        patch("homeassistant.components.elgato.config_flow.Elgato", new=elgato_mock),
    ):
        elgato = elgato_mock.return_value
        elgato.info.return_value = Info.from_json(
            load_fixture(f"{device_fixtures}/info.json", DOMAIN)
        )
        elgato.state.return_value = State.from_json(
            load_fixture(f"{device_fixtures}/{state_variant}.json", DOMAIN)
        )
        elgato.settings.return_value = Settings.from_json(
            load_fixture(f"{device_fixtures}/settings.json", DOMAIN)
        )

        if get_fixture_path(f"{device_fixtures}/battery.json", DOMAIN).exists():
            elgato.has_battery.return_value = True
            elgato.battery.return_value = BatteryInfo.from_json(
                load_fixture(f"{device_fixtures}/battery.json", DOMAIN)
            )
        else:
            elgato.has_battery.return_value = False
            elgato.battery.side_effect = ElgatoNoBatteryError

        yield elgato
