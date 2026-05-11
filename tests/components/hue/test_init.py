"""Test Hue setup process."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import aiohue.v2 as aiohue_v2
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import hue
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, async_get_persistent_notifications
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def mock_bridge_setup() -> Generator[Mock]:
    """Mock bridge setup."""
    with patch.object(hue, "HueBridge") as mock_bridge:
        mock_bridge.return_value.api_version = 2
        mock_bridge.return_value.async_initialize_bridge = AsyncMock(return_value=True)
        mock_bridge.return_value.api.config = Mock(
            bridge_id="mock-id",
            mac_address="00:00:00:00:00:00",
            model_id="BSB002",
            software_version="1.0.0",
            bridge_device=Mock(
                id="4a507550-8742-4087-8bf5-c2334f29891c",
                product_data=Mock(manufacturer_name="Mock"),
            ),
            spec=aiohue_v2.ConfigController,
        )
        mock_bridge.return_value.api.config.name = "Mock Hue bridge"
        yield mock_bridge.return_value


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_with_no_config(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we do not discover anything or try to set up a bridge."""
    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)

    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)

    expect(hass.config_entries.async_entries(hue.DOMAIN)).to_equal([])


@test
async def unload_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_setup: Mock = Depends(mock_bridge_setup),
) -> None:
    """Test being able to unload an entry."""
    entry = MockConfigEntry(
        domain=hue.DOMAIN, data={"host": "0.0.0.0", "api_version": 2}
    )
    entry.add_to_hass(hass)

    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)
    expect(len(mock_bridge_setup.mock_calls)).to_equal(1)

    entry.runtime_data = mock_bridge_setup

    async def mock_reset() -> bool:
        delattr(entry, "runtime_data")
        return True

    mock_bridge_setup.async_reset = mock_reset
    expect(await hue.async_unload_entry(hass, entry)).to_be(True)
    expect(hasattr(entry, "runtime_data")).to_be(False)


@test
async def setting_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_setup: Mock = Depends(mock_bridge_setup),
) -> None:
    """Test we set unique ID if not set yet."""
    entry = MockConfigEntry(
        domain=hue.DOMAIN, data={"host": "0.0.0.0", "api_version": 2}
    )
    entry.add_to_hass(hass)
    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)
    expect(entry.unique_id).to_equal("mock-id")


@test
async def fixing_unique_id_no_other(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_setup: Mock = Depends(mock_bridge_setup),
) -> None:
    """Test we set unique ID if not set yet."""
    entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0", "api_version": 2},
        unique_id="invalid-id",
    )
    entry.add_to_hass(hass)
    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)
    expect(entry.unique_id).to_equal("mock-id")


@test
async def fixing_unique_id_other_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_setup: Mock = Depends(mock_bridge_setup),
) -> None:
    """Test we set unique ID if not set yet."""
    MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0", "api_version": 2},
        unique_id="mock-id",
        source=config_entries.SOURCE_IGNORE,
    ).add_to_hass(hass)
    entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0", "api_version": 2},
        unique_id="invalid-id",
    )
    entry.add_to_hass(hass)
    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()
    expect(entry.unique_id).to_equal("mock-id")
    expect(hass.config_entries.async_entries()).to_equal([entry])


@test
async def fixing_unique_id_other_correct(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_bridge_setup: Mock = Depends(mock_bridge_setup),
) -> None:
    """Test we remove config entry if another one has correct ID."""
    correct_entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0", "api_version": 2},
        unique_id="mock-id",
    )
    correct_entry.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "0.0.0.0", "api_version": 2},
        unique_id="invalid-id",
    )
    entry.add_to_hass(hass)
    expect(await async_setup_component(hass, hue.DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries()).to_equal([correct_entry])


@test
async def security_vuln_check(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we report security vulnerabilities."""
    entry = MockConfigEntry(
        domain=hue.DOMAIN, data={"host": "0.0.0.0", "api_version": 1}
    )
    entry.add_to_hass(hass)

    config = Mock(
        bridge_id="",
        mac_address="",
        model_id="BSB002",
        software_version="1935144020",
    )
    config.name = "Hue"

    with (
        patch.object(hue.migration, "is_v2_bridge", return_value=False),
        patch.object(
            hue,
            "HueBridge",
            Mock(
                return_value=Mock(
                    async_initialize_bridge=AsyncMock(return_value=True),
                    api=Mock(config=config),
                    api_version=1,
                )
            ),
        ),
    ):
        expect(await async_setup_component(hass, "hue", {})).to_be(True)

    await hass.async_block_till_done()

    notifications = async_get_persistent_notifications(hass)
    expect("hue_hub_firmware" in notifications).to_be(True)
    expect("CVE-2020-6007" in notifications["hue_hub_firmware"]["message"]).to_be(True)
