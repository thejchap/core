"""Test discovery helpers."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import discovery
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from tests.common import MockModule, MockPlatform, mock_integration, mock_platform
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def listen(hass: HomeAssistant = Depends(hass)) -> None:
    """Test discovery listen/discover combo."""
    with patch(
        "homeassistant.setup.async_setup_component", return_value=True
    ) as mock_setup_component:
        calls_single = []

        @callback
        def callback_single(service, info):
            """Service discovered callback."""
            calls_single.append((service, info))

        discovery.async_listen(hass, "test service", callback_single)

        await discovery.async_discover(
            hass,
            "test service",
            "discovery info",
            "test_component",
            {},
        )
        await hass.async_block_till_done()

        expect(mock_setup_component.called).to_be(True)
        expect(mock_setup_component.call_args[0]).to_equal((hass, "test_component", {}))
        expect(len(calls_single)).to_equal(1)
        expect(calls_single[0]).to_equal(("test service", "discovery info"))


@test
async def platform(hass: HomeAssistant = Depends(hass)) -> None:
    """Test discover platform method."""
    with patch(
        "homeassistant.setup.async_setup_component", return_value=True
    ) as mock_setup_component:
        calls = []

        @callback
        def platform_callback(platform, info):
            """Platform callback method."""
            calls.append((platform, info))

        discovery.async_listen_platform(
            hass,
            "test_component",
            platform_callback,
        )

        await discovery.async_load_platform(
            hass,
            "test_component",
            "test_platform",
            "discovery info",
            {"test_component": {}},
        )
        await hass.async_block_till_done()
        expect(mock_setup_component.called).to_be(True)
        expect(mock_setup_component.call_args[0]).to_equal(
            (hass, "test_component", {"test_component": {}})
        )
        await hass.async_block_till_done()

        await hass.async_add_executor_job(
            discovery.load_platform,
            hass,
            "test_component_2",
            "test_platform",
            "discovery info",
            {"test_component": {}},
        )
        await hass.async_block_till_done()

        expect(len(calls)).to_equal(1)
        expect(calls[0]).to_equal(("test_platform", "discovery info"))

        async_dispatcher_send(
            hass,
            discovery.SIGNAL_PLATFORM_DISCOVERED,
            {"service": discovery.EVENT_LOAD_PLATFORM.format("test_component")},
        )
        await hass.async_block_till_done()

        expect(len(calls)).to_equal(1)


@test
async def circular_import(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we don't break doing circular import.

    This test will have test_component discover the switch.test_circular
    component while setting up.

    The supplied config will load test_component and will load
    switch.test_circular.

    That means that after startup, we will have test_component and switch
    setup. The test_circular platform has been loaded twice.
    """
    component_calls = []
    platform_calls = []

    def component_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up mock component."""
        discovery.load_platform(
            hass, Platform.SWITCH, "test_circular", {"key": "value"}, config
        )
        component_calls.append(1)
        return True

    def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities_callback: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up mock platform."""
        platform_calls.append("disc" if discovery_info else "component")

    mock_integration(hass, MockModule("test_component", setup=component_setup))

    # dependencies are only set in component level
    # since we are using manifest to hold them
    mock_integration(hass, MockModule("test_circular", dependencies=["test_component"]))
    mock_platform(
        hass, "test_circular.switch", MockPlatform(setup_platform=setup_platform)
    )

    await setup.async_setup_component(
        hass,
        "test_component",
        {"test_component": None, "switch": [{"platform": "test_circular"}]},
    )

    await hass.async_block_till_done()

    # test_component will only be setup once
    expect(len(component_calls)).to_equal(1)
    # The platform will be setup once via the config in `setup_component`
    # and once via the discovery inside test_component.
    expect(len(platform_calls)).to_equal(2)
    expect("test_component" in hass.config.components).to_be(True)
    expect("switch" in hass.config.components).to_be(True)


@test
async def _1st_discovers_2nd_component(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we don't break if one component discovers the other.

    If the first component fires a discovery event to set up the
    second component while the second component is about to be set up,
    it should not set up the second component twice.
    """
    component_calls = []

    async def component1_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up mock component."""
        await discovery.async_discover(
            hass, "test_component2", {}, "test_component2", {}
        )
        return True

    def component2_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up mock component."""
        component_calls.append(1)
        return True

    mock_integration(hass, MockModule("test_component1", async_setup=component1_setup))

    mock_integration(hass, MockModule("test_component2", setup=component2_setup))

    hass.async_create_task(setup.async_setup_component(hass, "test_component1", {}))
    hass.async_create_task(setup.async_setup_component(hass, "test_component2", {}))
    await hass.async_block_till_done()

    # test_component will only be setup once
    expect(len(component_calls)).to_equal(1)
