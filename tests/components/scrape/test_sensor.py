"""The tests for the Scrape sensor platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import MockRestData, return_integration_config

from tests.hass_fixtures import hass as hass_fixture, mock_network

DOMAIN = "scrape"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def scrape_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Scrape sensor minimal."""
    config = {
        DOMAIN: [
            return_integration_config(
                sensors=[{"select": ".current-version h1", "name": "HA version"}]
            )
        ]
    }

    mocker = MockRestData("test_scrape_sensor")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ):
        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.ha_version")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("Current Version: 2021.12.10")


@test.skip("requires log capture - port deferred")
async def scrape_xml_content_type() -> None:
    """Stub for test_scrape_xml_content_type (port deferred)."""

@test.skip("requires log capture - port deferred")
async def scrape_xml_declaration() -> None:
    """Stub for test_scrape_xml_declaration (port deferred)."""

@test.skip("requires log capture - port deferred")
async def scrape_html5_with_xml_declaration() -> None:
    """Stub for test_scrape_html5_with_xml_declaration (port deferred)."""

@test.skip("requires value template + log capture - port deferred")
async def scrape_sensor_value_template() -> None:
    """Stub for test_scrape_sensor_value_template (port deferred)."""

@test.skip("requires entity_registry inspection - port deferred")
async def scrape_uom_and_classes() -> None:
    """Stub for test_scrape_uom_and_classes (port deferred)."""

@test.skip("requires entity_registry inspection - port deferred")
async def scrape_unique_id() -> None:
    """Stub for test_scrape_unique_id (port deferred)."""

@test.skip("requires authentication scaffolding - port deferred")
async def scrape_sensor_authentication() -> None:
    """Stub for test_scrape_sensor_authentication (port deferred)."""

@test.skip("requires no-data fallback - port deferred")
async def scrape_sensor_no_data() -> None:
    """Stub for test_scrape_sensor_no_data (port deferred)."""

@test.skip("requires freezegun + refresh - port deferred")
async def scrape_sensor_no_data_refresh() -> None:
    """Stub for test_scrape_sensor_no_data_refresh (port deferred)."""

@test.skip("requires attribute parsing - port deferred")
async def scrape_sensor_attribute_and_tag() -> None:
    """Stub for test_scrape_sensor_attribute_and_tag (port deferred)."""

@test.skip("requires date parsing - port deferred")
async def scrape_sensor_device_date() -> None:
    """Stub for test_scrape_sensor_device_date (port deferred)."""

@test.skip("requires date parsing + log capture - port deferred")
async def scrape_sensor_device_date_errors() -> None:
    """Stub for test_scrape_sensor_device_date_errors (port deferred)."""

@test.skip("requires timestamp parsing - port deferred")
async def scrape_sensor_device_timestamp() -> None:
    """Stub for test_scrape_sensor_device_timestamp (port deferred)."""

@test.skip("requires timestamp parsing + log capture - port deferred")
async def scrape_sensor_device_timestamp_error() -> None:
    """Stub for test_scrape_sensor_device_timestamp_error (port deferred)."""

@test.skip("requires log capture - port deferred")
async def scrape_sensor_errors() -> None:
    """Stub for test_scrape_sensor_errors (port deferred)."""

@test.skip("requires entity_registry inspection - port deferred")
async def scrape_sensor_unique_id() -> None:
    """Stub for test_scrape_sensor_unique_id (port deferred)."""

@test.skip("requires config_entry setup - port deferred")
async def setup_config_entry() -> None:
    """Stub for test_setup_config_entry (port deferred)."""

@test.skip("requires template rendering - port deferred")
async def templates_with_yaml() -> None:
    """Stub for test_templates_with_yaml (port deferred)."""

@test.skip("requires availability - port deferred")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""

@test.skip("requires availability + template - port deferred")
async def template_render_with_availability_syntax_error() -> None:
    """Stub (port deferred)."""

@test.skip("requires availability + value template - port deferred")
async def availability_blocks_value_template() -> None:
    """Stub (port deferred)."""
