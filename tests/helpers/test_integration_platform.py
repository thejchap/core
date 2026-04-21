"""Test integration platform helpers."""

from collections.abc import Callable
from types import ModuleType
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.integration_platform import (
    async_process_integration_platforms,
)
from homeassistant.setup import ATTR_COMPONENT

from tests.common import mock_platform
from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def process_integration_platforms_with_wait(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test processing integrations."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded.platform_to_check", loaded_platform)
    hass.config.components.add("loaded")

    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    await async_process_integration_platforms(
        hass, "platform_to_check", _process_platform, wait_for_platforms=True
    )

    expect(len(processed)).to_equal(1)
    expect(processed[0][0]).to_equal("loaded")
    expect(processed[0][1]).to_equal(loaded_platform)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(2)
    expect(processed[1][0]).to_equal("event")
    expect(processed[1][1]).to_equal(event_platform)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(2)


@test
async def process_integration_platforms(hass: HomeAssistant = Depends(hass)) -> None:
    """Test processing integrations."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded.platform_to_check", loaded_platform)
    hass.config.components.add("loaded")

    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    await async_process_integration_platforms(
        hass, "platform_to_check", _process_platform
    )
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(1)
    expect(processed[0][0]).to_equal("loaded")
    expect(processed[0][1]).to_equal(loaded_platform)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(2)
    expect(processed[1][0]).to_equal("event")
    expect(processed[1][1]).to_equal(event_platform)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(2)


@test
async def process_integration_platforms_import_fails(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test processing integrations when one fails to import."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded.platform_to_check", loaded_platform)
    hass.config.components.add("loaded")

    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    loaded_integration = await loader.async_get_integration(hass, "loaded")
    with patch.object(
        loaded_integration, "async_get_platform", side_effect=ImportError
    ):
        await async_process_integration_platforms(
            hass, "platform_to_check", _process_platform
        )
        await hass.async_block_till_done()

    expect(len(processed)).to_equal(0)
    expect(
        "Unexpected error importing platform_to_check for loaded" in caplog.text
    ).to_be(True)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(1)
    expect(processed[0][0]).to_equal("event")
    expect(processed[0][1]).to_equal(event_platform)

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(1)


@test
async def process_integration_platforms_import_fails_after_registered(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test processing integrations when one fails to import."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded.platform_to_check", loaded_platform)
    hass.config.components.add("loaded")

    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    await async_process_integration_platforms(
        hass, "platform_to_check", _process_platform
    )
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(1)
    expect(processed[0][0]).to_equal("loaded")
    expect(processed[0][1]).to_equal(loaded_platform)

    event_integration = await loader.async_get_integration(hass, "event")
    with (
        patch.object(event_integration, "async_get_platforms", side_effect=ImportError),
        patch.object(event_integration, "get_platform_cached", return_value=None),
    ):
        hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
        await hass.async_block_till_done()

    expect(len(processed)).to_equal(1)
    expect(
        "Unexpected error importing integration platforms for event" in caplog.text
    ).to_be(True)


@callback
def _process_platform_callback(
    hass: HomeAssistant, domain: str, platform: ModuleType
) -> None:
    """Process platform."""
    raise HomeAssistantError("Non-compliant platform")


async def _process_platform_coro(
    hass: HomeAssistant, domain: str, platform: ModuleType
) -> None:
    """Process platform."""
    raise HomeAssistantError("Non-compliant platform")


@test.cases(
    test.case("_process_platform_callback", process_platform=_process_platform_callback),
    test.case("_process_platform_coro", process_platform=_process_platform_coro),
)
async def process_integration_platforms_non_compliant(
    process_platform: Callable,
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test processing integrations using with a non-compliant platform."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded_unique_880.platform_to_check", loaded_platform)
    hass.config.components.add("loaded_unique_880")

    event_platform = Mock()
    mock_platform(hass, "event_unique_990.platform_to_check", event_platform)

    processed = []

    await async_process_integration_platforms(
        hass, "platform_to_check", process_platform
    )
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(0)
    expect("Exception in " in caplog.text).to_be(True)
    expect("platform_to_check" in caplog.text).to_be(True)
    expect("Non-compliant platform" in caplog.text).to_be(True)
    expect("loaded_unique_880" in caplog.text).to_be(True)
    caplog.clear()

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event_unique_990"})
    await hass.async_block_till_done()

    expect("Exception in " in caplog.text).to_be(True)
    expect("platform_to_check" in caplog.text).to_be(True)
    expect("Non-compliant platform" in caplog.text).to_be(True)
    expect("event_unique_990" in caplog.text).to_be(True)

    expect(len(processed)).to_equal(0)


@test
async def broken_integration(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test handling an integration with a broken or missing manifest."""
    Mock()
    hass.config.components.add("loaded")

    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    await async_process_integration_platforms(
        hass, "platform_to_check", _process_platform
    )
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(0)


@test
async def process_integration_platforms_no_integrations(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test processing integrations when no integrations are loaded."""
    event_platform = Mock()
    mock_platform(hass, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform(
        hass: HomeAssistant, domain: str, platform: Any
    ) -> None:
        """Process platform."""
        processed.append((domain, platform))

    await async_process_integration_platforms(
        hass, "platform_to_check", _process_platform
    )
    await hass.async_block_till_done()

    expect(len(processed)).to_equal(0)
