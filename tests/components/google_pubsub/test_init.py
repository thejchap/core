"""The tests for the Google Pub/Sub component."""

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components import google_pubsub
from homeassistant.components.google_pubsub import DateTimeJSONEncoder as victim
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mock_client as mock_client_fixture,
    mock_is_file as mock_is_file_fixture,
    mock_json as mock_json_fixture,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@dataclass
class FilterTest:
    """Class for capturing a filter test."""

    id: str
    should_pass: bool


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_is_file: MagicMock = Depends(mock_is_file_fixture),
    _mock_json: None = Depends(mock_json_fixture),
) -> HomeAssistant:
    """Force tryke to build a HookExecutor and resolve autouse fixtures.

    Requests ``hass`` before applying the ``os.path.isfile`` mock so HA's
    zoneinfo lookup during ``async_set_time_zone`` doesn't see the patched
    isfile and stub-loaded files.
    """
    return hass


@test
async def datetime_test() -> None:
    """Test datetime encoding."""
    time = datetime(2019, 1, 13, 12, 30, 5)
    expect(victim().encode(time)).to_equal('"2019-01-13T12:30:05"')


@test
async def no_datetime() -> None:
    """Test integer encoding."""
    expect(victim().encode(42)).to_equal("42")


@test
async def nested() -> None:
    """Test dictionary encoding."""
    expect(victim().encode({"foo": "bar"})).to_equal('{"foo": "bar"}')


@test
async def minimal_config(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
) -> None:
    """Test the minimal config and defaults of component."""
    config = {
        google_pubsub.DOMAIN: {
            "project_id": "proj",
            "topic_name": "topic",
            "credentials_json": "creds",
            "filter": {},
        }
    }
    expect(await async_setup_component(hass, google_pubsub.DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()
    expect(mock_client.from_service_account_json.call_count).to_equal(1)
    expect(mock_client.from_service_account_json.call_args[0][0]).to_equal(
        os.path.join(hass.config.config_dir, "creds")
    )


@test
async def full_config(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
) -> None:
    """Test the full config of the component."""
    config = {
        google_pubsub.DOMAIN: {
            "project_id": "proj",
            "topic_name": "topic",
            "credentials_json": "creds",
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
    expect(await async_setup_component(hass, google_pubsub.DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()
    expect(mock_client.from_service_account_json.call_count).to_equal(1)
    expect(mock_client.from_service_account_json.call_args[0][0]).to_equal(
        os.path.join(hass.config.config_dir, "creds")
    )


async def _setup(hass: HomeAssistant, filter_config: dict[str, Any]) -> None:
    """Shared set up for filtering tests."""
    config = {
        google_pubsub.DOMAIN: {
            "project_id": "proj",
            "topic_name": "topic",
            "credentials_json": "creds",
            "filter": filter_config,
        }
    }
    expect(await async_setup_component(hass, google_pubsub.DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()


@test
async def allowlist(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
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
    publish_client = mock_client.from_service_account_json("path")

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    for t in tests:
        hass.states.async_set(t.id, "on")
        await hass.async_block_till_done()

        was_called = publish_client.publish.call_count == 1
        expect(t.should_pass).to_equal(was_called)
        publish_client.publish.reset_mock()


@test
async def denylist(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
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
    publish_client = mock_client.from_service_account_json("path")

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("light.included", True),
        FilterTest("sensor.excluded_test", False),
        FilterTest("sensor.included_test", True),
        FilterTest("binary_sensor.included", True),
        FilterTest("binary_sensor.excluded", False),
    ]

    for t in tests:
        hass.states.async_set(t.id, "on")
        await hass.async_block_till_done()

        was_called = publish_client.publish.call_count == 1
        expect(t.should_pass).to_equal(was_called)
        publish_client.publish.reset_mock()


@test
async def filtered_allowlist(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
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
    publish_client = mock_client.from_service_account_json("path")

    tests = [
        FilterTest("light.included", True),
        FilterTest("light.excluded_test", False),
        FilterTest("light.excluded", False),
        FilterTest("sensor.included_test", True),
        FilterTest("climate.included_test", True),
    ]

    for t in tests:
        hass.states.async_set(t.id, "not blank")
        await hass.async_block_till_done()

        was_called = publish_client.publish.call_count == 1
        expect(t.should_pass).to_equal(was_called)
        publish_client.publish.reset_mock()


@test
async def filtered_denylist(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: MagicMock = Depends(mock_client_fixture),
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
    publish_client = mock_client.from_service_account_json("path")

    tests = [
        FilterTest("climate.excluded", False),
        FilterTest("climate.included", True),
        FilterTest("switch.excluded_test", False),
        FilterTest("sensor.excluded_test", True),
        FilterTest("light.excluded", False),
        FilterTest("light.included", True),
    ]

    for t in tests:
        hass.states.async_set(t.id, "not blank")
        await hass.async_block_till_done()

        was_called = publish_client.publish.call_count == 1
        expect(t.should_pass).to_equal(was_called)
        publish_client.publish.reset_mock()
