"""Test Home Assistant icon util methods."""

import pathlib
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.core import HomeAssistant
from homeassistant.helpers import icon
from homeassistant.loader import IntegrationNotFound
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def battery_icon() -> None:
    """Test icon generator for battery sensor."""
    expect(icon.icon_for_battery_level(None, True)).to_equal("mdi:battery-unknown")
    expect(icon.icon_for_battery_level(None, False)).to_equal("mdi:battery-unknown")

    expect(icon.icon_for_battery_level(5, True)).to_equal("mdi:battery-outline")
    expect(icon.icon_for_battery_level(5, False)).to_equal("mdi:battery-alert")

    expect(icon.icon_for_battery_level(100, True)).to_equal("mdi:battery-charging-100")
    expect(icon.icon_for_battery_level(100, False)).to_equal("mdi:battery")

    iconbase = "mdi:battery"
    for level in range(0, 100, 5):
        if level <= 10:
            postfix_charging = "-outline"
        elif level <= 30:
            postfix_charging = "-charging-20"
        elif level <= 50:
            postfix_charging = "-charging-40"
        elif level <= 70:
            postfix_charging = "-charging-60"
        elif level <= 90:
            postfix_charging = "-charging-80"
        else:
            postfix_charging = "-charging-100"
        if 5 < level < 95:
            postfix = f"-{int(round(level / 10 - 0.01)) * 10}"
        elif level <= 5:
            postfix = "-alert"
        else:
            postfix = ""
        expect(icon.icon_for_battery_level(level, False)).to_equal(iconbase + postfix)
        expect(icon.icon_for_battery_level(level, True)).to_equal(
            iconbase + postfix_charging
        )


@test
def signal_icon() -> None:
    """Test icon generator for signal sensor."""
    expect(icon.icon_for_signal_level(None)).to_equal("mdi:signal-cellular-outline")
    expect(icon.icon_for_signal_level(0)).to_equal("mdi:signal-cellular-outline")
    expect(icon.icon_for_signal_level(5)).to_equal("mdi:signal-cellular-1")
    expect(icon.icon_for_signal_level(40)).to_equal("mdi:signal-cellular-2")
    expect(icon.icon_for_signal_level(80)).to_equal("mdi:signal-cellular-3")
    expect(icon.icon_for_signal_level(100)).to_equal("mdi:signal-cellular-3")


@test
async def load_icons_files(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the load icons files function."""
    file1 = hass.config.path("custom_components", "test", "icons.json")
    file2 = hass.config.path("custom_components", "test", "invalid.json")
    expect(icon._load_icons_files({"test": file1, "invalid": file2})).to_equal(
        {
            "test": {
                "entity": {
                    "switch": {
                        "something": {
                            "state": {"away": "mdi:home-outline", "home": "mdi:home"}
                        }
                    }
                },
            },
            "invalid": {},
        }
    )


@test
async def get_icons(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the get icon helper."""
    # Inline enable_custom_integrations behavior.
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)

    icons = await icon.async_get_icons(hass, "entity")
    expect(icons).to_equal({})

    icons = await icon.async_get_icons(hass, "entity_component")
    expect(icons).to_equal({})

    # Set up test switch component
    expect(
        await async_setup_component(hass, "switch", {"switch": {"platform": "test"}})
    ).to_be(True)

    # Test getting icons for the entity component
    icons = await icon.async_get_icons(hass, "entity_component")
    expect(icons["switch"]["_"]["default"]).to_equal("mdi:toggle-switch-variant")

    # Test services icons are available
    icons = await icon.async_get_icons(hass, "services")
    expect(len(icons)).to_equal(1)
    expect(icons["switch"]["turn_off"]).to_equal(
        {"service": "mdi:toggle-switch-variant-off"}
    )

    # Ensure icons file for platform isn't loaded, as that isn't supported
    icons = await icon.async_get_icons(hass, "entity")
    expect(icons).to_equal({})

    async def _get_entity_test_switch() -> None:
        await icon.async_get_icons(hass, "entity", ["test.switch"])

    try:
        await _get_entity_test_switch()
    except ValueError as err:
        expect("test.switch" in str(err)).to_be(True)
    else:
        expect("raised ValueError").to_equal("no exception")

    # Load up an custom integration
    hass.config.components.add("test_package")
    await hass.async_block_till_done()

    icons = await icon.async_get_icons(hass, "entity")
    expect(len(icons)).to_equal(1)

    expect(icons).to_equal(
        {
            "test_package": {
                "switch": {
                    "something": {
                        "state": {"away": "mdi:home-outline", "home": "mdi:home"}
                    }
                }
            }
        }
    )

    icons = await icon.async_get_icons(hass, "services")
    expect(len(icons)).to_equal(2)
    expect(icons["test_package"]["enable_god_mode"]).to_equal(
        {"service": "mdi:shield"}
    )

    # Load another one
    hass.config.components.add("test_embedded")
    await hass.async_block_till_done()

    icons = await icon.async_get_icons(hass, "entity")
    expect(len(icons)).to_equal(2)

    expect(icons["test_package"]).to_equal(
        {
            "switch": {
                "something": {"state": {"away": "mdi:home-outline", "home": "mdi:home"}}
            }
        }
    )

    # Test getting non-existing integration
    try:
        await icon.async_get_icons(hass, "entity", ["non_existing"])
    except IntegrationNotFound as err:
        expect("Integration 'non_existing' not found" in str(err)).to_be(True)
    else:
        expect("raised IntegrationNotFound").to_equal("no exception")


@test
async def get_icons_while_loading_components(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the get icons helper loads icons."""
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 1"
    hass.config.components.add("component1")
    load_count = 0

    def mock_load_icons_files(files):
        """Mock load icon files."""
        nonlocal load_count
        load_count += 1
        return {"component1": {"entity": {"climate": {"test": {"icon": "mdi:home"}}}}}

    with (
        patch(
            "homeassistant.helpers.icon._load_icons_files",
            mock_load_icons_files,
        ),
        patch(
            "homeassistant.helpers.icon.async_get_integrations",
            return_value={"component1": integration},
        ),
    ):
        times = 5
        all_icons = [await icon.async_get_icons(hass, "entity") for _ in range(times)]

    expect(all_icons).to_equal(
        [
            {"component1": {"climate": {"test": {"icon": "mdi:home"}}}}
            for _ in range(times)
        ]
    )
    expect(load_count).to_equal(1)


@test
async def caching(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we cache data."""
    hass.config.components.add("binary_sensor")
    hass.config.components.add("switch")

    # Patch with same method so we can count invocations
    with patch(
        "homeassistant.helpers.icon.build_resources",
        side_effect=icon.build_resources,
    ) as mock_build:
        load1 = await icon.async_get_icons(hass, "entity_component")
        # conditions, entity_component, services, triggers
        expect(len(mock_build.mock_calls)).to_equal(4)

        load2 = await icon.async_get_icons(hass, "entity_component")
        # conditions, entity_component, services, triggers
        expect(len(mock_build.mock_calls)).to_equal(4)

        expect(load1).to_equal(load2)

        expect(bool(load1["binary_sensor"])).to_be(True)
        expect(bool(load1["switch"])).to_be(True)

    load_switch_only = await icon.async_get_icons(
        hass, "entity_component", integrations={"switch"}
    )
    expect(bool(load_switch_only)).to_be(True)
    expect(list(load_switch_only)).to_equal(["switch"])

    load_binary_sensor_only = await icon.async_get_icons(
        hass, "entity_component", integrations={"binary_sensor"}
    )
    expect(bool(load_binary_sensor_only)).to_be(True)
    expect(list(load_binary_sensor_only)).to_equal(["binary_sensor"])

    # Check if new loaded component, trigger load
    hass.config.components.add("media_player")
    with patch(
        "homeassistant.helpers.icon._load_icons_files",
        side_effect=icon._load_icons_files,
    ) as mock_load:
        load_sensor_only = await icon.async_get_icons(
            hass, "entity_component", integrations={"switch"}
        )
        expect(bool(load_sensor_only)).to_be(True)
        expect(len(mock_load.mock_calls)).to_equal(0)

        await icon.async_get_icons(
            hass, "entity_component", integrations={"media_player"}
        )
        expect(len(mock_load.mock_calls)).to_equal(1)
