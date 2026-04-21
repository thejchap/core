"""Tests for the reload helper."""

import logging
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigValidationError, HomeAssistantError
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers.reload import (
    async_get_platform_without_config_entry,
    async_integration_yaml_config,
    async_reload_integration_platforms,
    async_setup_reload_service,
)
from homeassistant.loader import async_get_integration

from tests.common import (
    MockModule,
    MockPlatform,
    get_fixture_path,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import hass

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"
PLATFORM = "test_platform"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def reload_platform(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the polling of only updated entities."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    expect(component_setup.called).to_be(True)

    expect(f"{PLATFORM}.{DOMAIN}" in hass.config.components).to_be(True)
    expect(len(setup_called)).to_equal(1)

    platform = async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)
    expect(platform.platform_name).to_equal(PLATFORM)
    expect(platform.domain).to_equal(DOMAIN)

    yaml_path = get_fixture_path("helpers/reload_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await async_reload_integration_platforms(hass, PLATFORM, [DOMAIN])

    expect(len(setup_called)).to_equal(2)

    existing_platforms = async_get_platforms(hass, PLATFORM)
    for existing_platform in existing_platforms:
        existing_platform.config_entry = "abc"
    expect(async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)).to_be_none()


@test
async def setup_reload_service(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setting up a reload service."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    expect(component_setup.called).to_be(True)

    expect(f"{PLATFORM}.{DOMAIN}" in hass.config.components).to_be(True)
    expect(len(setup_called)).to_equal(1)

    await async_setup_reload_service(hass, PLATFORM, [DOMAIN])

    yaml_path = get_fixture_path("helpers/reload_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(setup_called)).to_equal(2)


@test
async def setup_reload_service_when_async_process_component_config_fails(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setting up a reload service with the config processing failing."""
    component_setup = Mock(return_value=True)

    setup_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    expect(component_setup.called).to_be(True)

    expect(f"{PLATFORM}.{DOMAIN}" in hass.config.components).to_be(True)
    expect(len(setup_called)).to_equal(1)

    await async_setup_reload_service(hass, PLATFORM, [DOMAIN])

    yaml_path = get_fixture_path("helpers/reload_configuration.yaml")
    with (
        patch.object(config, "YAML_CONFIG_FILE", yaml_path),
        patch.object(
            config,
            "async_process_component_config",
            return_value=config.IntegrationConfigInfo(None, []),
        ),
    ):
        await hass.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(setup_called)).to_equal(1)


@test
async def setup_reload_service_with_platform_that_provides_async_reset_platform(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setting up a reload service using a platform that has its own async_reset_platform."""
    component_setup = AsyncMock(return_value=True)

    setup_called = []
    async_reset_platform_called = []

    async def setup_platform(*args):
        setup_called.append(args)

    async def async_reset_platform(*args):
        async_reset_platform_called.append(args)

    mock_integration(hass, MockModule(DOMAIN, async_setup=component_setup))
    integration = await async_get_integration(hass, DOMAIN)
    integration.get_component().async_reset_platform = async_reset_platform

    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "name": "xyz"}})
    await hass.async_block_till_done()
    expect(component_setup.called).to_be(True)

    expect(f"{PLATFORM}.{DOMAIN}" in hass.config.components).to_be(True)
    expect(len(setup_called)).to_equal(1)

    await async_setup_reload_service(hass, PLATFORM, [DOMAIN])

    yaml_path = get_fixture_path("helpers/reload_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            PLATFORM,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(setup_called)).to_equal(1)
    expect(len(async_reset_platform_called)).to_equal(1)


@test
async def async_integration_yaml_config_(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading yaml config for an integration."""
    mock_integration(hass, MockModule(DOMAIN))

    yaml_path = get_fixture_path(f"helpers/{DOMAIN}_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        processed_config = await async_integration_yaml_config(hass, DOMAIN)
        expect(processed_config).to_equal({DOMAIN: [{"name": "one"}, {"name": "two"}]})
        # Test fetching yaml config does not raise when the raise_on_failure option is set
        processed_config = await async_integration_yaml_config(
            hass, DOMAIN, raise_on_failure=True
        )
        expect(processed_config).to_equal({DOMAIN: [{"name": "one"}, {"name": "two"}]})


@test
async def async_integration_failing_yaml_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test reloading yaml config for an integration fails."""
    schema_without_name_attr = vol.Schema({vol.Required("some_option"): str})

    mock_integration(hass, MockModule(DOMAIN, config_schema=schema_without_name_attr))

    yaml_path = get_fixture_path(f"helpers/{DOMAIN}_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        # Test fetching yaml config does not raise without raise_on_failure option
        processed_config = await async_integration_yaml_config(hass, DOMAIN)
        expect(processed_config).to_be_none()
        # Test fetching yaml config does not raise when the raise_on_failure option is set
        try:
            await async_integration_yaml_config(hass, DOMAIN, raise_on_failure=True)
        except ConfigValidationError:
            pass
        else:
            expect("raised ConfigValidationError").to_equal("no exception")


@test
async def async_integration_failing_on_reload(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test reloading yaml config for an integration fails with an other exception."""
    mock_integration(hass, MockModule(DOMAIN))

    yaml_path = get_fixture_path(f"helpers/{DOMAIN}_configuration.yaml")
    with (
        patch.object(config, "YAML_CONFIG_FILE", yaml_path),
        patch(
            "homeassistant.config.async_process_component_config",
            side_effect=HomeAssistantError(),
        ),
    ):
        try:
            await async_integration_yaml_config(hass, DOMAIN, raise_on_failure=True)
        except HomeAssistantError:
            pass
        else:
            expect("raised HomeAssistantError").to_equal("no exception")


@test
async def async_integration_missing_yaml_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading missing yaml config for an integration."""
    mock_integration(hass, MockModule(DOMAIN))

    yaml_path = get_fixture_path("helpers/does_not_exist_configuration.yaml")
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        try:
            await async_integration_yaml_config(hass, DOMAIN)
        except FileNotFoundError:
            pass
        else:
            expect("raised FileNotFoundError").to_equal("no exception")
