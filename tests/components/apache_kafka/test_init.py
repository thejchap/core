"""The tests for the Apache Kafka component."""

from dataclasses import dataclass
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import apache_kafka
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import MockKafkaClient, mock_client

from tests.hass_fixtures import hass as hass_fixture, mock_network

MIN_CONFIG = {
    "ip_address": "localhost",
    "port": 8080,
    "topic": "topic",
}


@dataclass
class FilterTest:
    """Class for capturing a filter test."""

    id: str
    should_pass: bool


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def minimal_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test the minimal config and defaults of component."""
    config = {apache_kafka.DOMAIN: MIN_CONFIG}
    expect(await async_setup_component(hass, apache_kafka.DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()
    client.start.assert_called_once()


@test
async def full_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test the full config of component."""
    config = {
        apache_kafka.DOMAIN: {
            "filter": {
                "include_domains": ["light"],
                "include_entity_globs": ["sensor.included_*"],
                "include_entities": ["binary_sensor.included"],
                "exclude_domains": ["light"],
                "exclude_entity_globs": ["sensor.excluded_*"],
                "exclude_entities": ["binary_sensor.excluded"],
            },
        }
    }
    config[apache_kafka.DOMAIN].update(MIN_CONFIG)

    expect(await async_setup_component(hass, apache_kafka.DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()
    client.start.assert_called_once()


async def _setup(hass: HomeAssistant, filter_config: dict[str, Any]) -> None:
    """Shared set up for filtering tests."""
    config = {apache_kafka.DOMAIN: {"filter": filter_config}}
    config[apache_kafka.DOMAIN].update(MIN_CONFIG)

    assert await async_setup_component(hass, apache_kafka.DOMAIN, config)
    await hass.async_block_till_done()


async def _run_filter_tests(
    hass: HomeAssistant, tests: list[FilterTest], client: MockKafkaClient
) -> None:
    """Run a series of filter tests on apache kafka."""
    for case in tests:
        hass.states.async_set(case.id, STATE_ON)
        await hass.async_block_till_done()

        if case.should_pass:
            client.send_and_wait.assert_called_once()
            client.send_and_wait.reset_mock()
        else:
            client.send_and_wait.assert_not_called()


@test
async def allowlist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test an allowlist only config."""
    await _setup(
        hass,
        {
            "include_domains": ["light"],
            "include_entity_globs": ["sensor.included_*"],
            "include_entities": ["binary_sensor.included"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    await _run_filter_tests(hass, tests, client)


@test
async def denylist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test a denylist only config."""
    await _setup(
        hass,
        {
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["sensor.excluded_*"],
            "exclude_entities": ["binary_sensor.excluded"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    await _run_filter_tests(hass, tests, client)


@test
async def filtered_allowlist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test an allowlist config with a filtering denylist."""
    await _setup(
        hass,
        {
            "include_domains": ["light"],
            "include_entity_globs": ["*.included_*"],
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["*.excluded_*"],
            "exclude_entities": ["light.excluded"],
        },
    )

    tests = [
        FilterTest("light.included", True),
        FilterTest("light.excluded_test", False),
        FilterTest("light.excluded", False),
        FilterTest("sensor.included_test", True),
        FilterTest("climate.included_test", True),
    ]

    await _run_filter_tests(hass, tests, client)


@test
async def filtered_denylist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockKafkaClient = Depends(mock_client),
) -> None:
    """Test a denylist config with a filtering allowlist."""
    await _setup(
        hass,
        {
            "include_entities": ["climate.included", "sensor.excluded_test"],
            "exclude_domains": ["climate"],
            "exclude_entity_globs": ["*.excluded_*"],
            "exclude_entities": ["light.excluded"],
        },
    )

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("climate.included", True),
        FilterTest("switch.excluded_test", False),
        FilterTest("sensor.excluded_test", True),
        FilterTest("light.excluded", False),
        FilterTest("light.included", True),
    ]

    await _run_filter_tests(hass, tests, client)


_ = (mock_client,)
