"""Tests for rest component."""

from datetime import timedelta
import ssl
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components.rest.const import DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_PACKAGES,
    SERVICE_RELOAD,
    STATE_UNAVAILABLE,
    UnitOfInformation,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from tests.common import (
    assert_setup_component,
    async_fire_time_changed,
    get_fixture_path,
)
from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@test
async def setup_with_endpoint_timeout_with_recovery(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with an endpoint that times out that recovers."""
    await async_setup_component(hass, "homeassistant", {})

    aioclient_mock.get("http://localhost", exc=TimeoutError())
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor1",
                                "value_template": "{{ value_json.sensor1 }}",
                            },
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor2",
                                "value_template": "{{ value_json.sensor2 }}",
                            },
                        ],
                        "binary_sensor": [
                            {
                                "name": "binary_sensor1",
                                "value_template": "{{ value_json.binary_sensor1 }}",
                            },
                            {
                                "name": "binary_sensor2",
                                "value_template": "{{ value_json.binary_sensor2 }}",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(0)

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    # Refresh the coordinator
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    # Wait for platform setup retry
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(4)

    expect(hass.states.get("sensor.sensor1").state).to_equal("1")
    expect(hass.states.get("sensor.sensor2").state).to_equal("2")
    expect(hass.states.get("binary_sensor.binary_sensor1").state).to_equal("on")
    expect(hass.states.get("binary_sensor.binary_sensor2").state).to_equal("off")

    # Now the end point flakes out again
    aioclient_mock.clear_requests()
    aioclient_mock.get("http://localhost", exc=TimeoutError())

    # Refresh the coordinator
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.sensor1").state).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get("sensor.sensor2").state).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get("binary_sensor.binary_sensor1").state).to_equal(
        STATE_UNAVAILABLE
    )
    expect(hass.states.get("binary_sensor.binary_sensor2").state).to_equal(
        STATE_UNAVAILABLE
    )

    # We request a manual refresh when the
    # endpoint is working again

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.sensor1"]},
        blocking=True,
    )
    expect(hass.states.get("sensor.sensor1").state).to_equal("1")
    expect(hass.states.get("sensor.sensor2").state).to_equal("2")
    expect(hass.states.get("binary_sensor.binary_sensor1").state).to_equal("on")
    expect(hass.states.get("binary_sensor.binary_sensor2").state).to_equal("off")


@test
async def setup_with_ssl_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup with an ssl error."""
    await async_setup_component(hass, "homeassistant", {})

    aioclient_mock.get("https://localhost", exc=ssl.SSLError("ssl error"))
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "https://localhost",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor1",
                                "value_template": "{{ value_json.sensor1 }}",
                            },
                        ],
                        "binary_sensor": [
                            {
                                "name": "binary_sensor1",
                                "value_template": "{{ value_json.binary_sensor1 }}",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(0)
    expect(caplog.text).to_contain("ssl error")


@test
async def setup_minimum_resource_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with minimum configuration (resource_template)."""

    aioclient_mock.get(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource_template": "{% set url = 'http://localhost' %}{{ url }}",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor1",
                                "value_template": "{{ value_json.sensor1 }}",
                            },
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor2",
                                "value_template": "{{ value_json.sensor2 }}",
                            },
                        ],
                        "binary_sensor": [
                            {
                                "name": "binary_sensor1",
                                "value_template": "{{ value_json.binary_sensor1 }}",
                            },
                            {
                                "name": "binary_sensor2",
                                "value_template": "{{ value_json.binary_sensor2 }}",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(4)

    expect(hass.states.get("sensor.sensor1").state).to_equal("1")
    expect(hass.states.get("sensor.sensor2").state).to_equal("2")
    expect(hass.states.get("binary_sensor.binary_sensor1").state).to_equal("on")
    expect(hass.states.get("binary_sensor.binary_sensor2").state).to_equal("off")


@test
async def reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify we can reload."""

    aioclient_mock.get("http://localhost", text="")

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "name": "mockrest",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(1)

    expect(hass.states.get("sensor.mockrest")).not_.to_be_none()

    yaml_path = get_fixture_path("configuration_top_level.yaml", "rest")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.mockreset")).to_be_none()
    expect(hass.states.get("sensor.rollout")).not_.to_be_none()
    expect(hass.states.get("sensor.fallover")).not_.to_be_none()


@test
async def reload_and_remove_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify we can reload and remove all."""

    aioclient_mock.get("http://localhost", text="")

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "name": "mockrest",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(1)

    expect(hass.states.get("sensor.mockrest")).not_.to_be_none()

    yaml_path = get_fixture_path("configuration_empty.yaml", "rest")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.mockreset")).to_be_none()


@test
async def reload_fails_to_read_configuration(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Verify reload when configuration is missing or broken."""

    aioclient_mock.get("http://localhost", text="")

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "method": "GET",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "name": "mockrest",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(1)

    yaml_path = get_fixture_path("configuration_invalid.notyaml", "rest")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "rest",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(1)


@test
async def multiple_rest_endpoints(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test multiple rest endpoints."""

    aioclient_mock.get(
        "http://date.jsontest.com",
        json={
            "date": "03-17-2021",
            "milliseconds_since_epoch": 1616008268573,
            "time": "07:11:08 PM",
        },
    )

    aioclient_mock.get(
        "http://time.jsontest.com",
        json={
            "date": "03-17-2021",
            "milliseconds_since_epoch": 1616008299665,
            "time": "07:11:39 PM",
        },
    )
    aioclient_mock.get(
        "http://localhost",
        json={
            "value": "1",
        },
    )
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://date.jsontest.com",
                        "sensor": [
                            {
                                "name": "JSON Date",
                                "value_template": "{{ value_json.date }}",
                            },
                            {
                                "name": "JSON Date Time",
                                "value_template": "{{ value_json.time }}",
                            },
                        ],
                    },
                    {
                        "resource": "http://time.jsontest.com",
                        "sensor": [
                            {
                                "name": "JSON Time",
                                "value_template": "{{ value_json.time }}",
                            },
                        ],
                    },
                    {
                        "resource": "http://localhost",
                        "binary_sensor": [
                            {
                                "name": "Binary Sensor",
                                "value_template": "{{ value_json.value }}",
                            },
                        ],
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(4)

    expect(hass.states.get("sensor.json_date").state).to_equal("03-17-2021")
    expect(hass.states.get("sensor.json_date_time").state).to_equal("07:11:08 PM")
    expect(hass.states.get("sensor.json_time").state).to_equal("07:11:39 PM")
    expect(hass.states.get("binary_sensor.binary_sensor").state).to_equal("on")


@test
async def empty_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with empty configuration.

    For example (with rest.yaml an empty file):
        rest: !include rest.yaml
    """
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {}},
        )
    ).to_be_truthy()
    assert_setup_component(0, DOMAIN)


@test
async def config_schema_via_packages(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration via packages."""
    packages = {
        "pack_dict": {"rest": {}},
        "pack_11": {"rest": {"resource": "http://url1"}},
        "pack_list": {"rest": [{"resource": "http://url2"}]},
    }
    config = {HOMEASSISTANT_DOMAIN: {CONF_PACKAGES: packages}}
    await hass_config.merge_packages_config(hass, config, packages)

    expect(len(config)).to_equal(2)
    expect(len(config["rest"])).to_equal(2)
    expect(config["rest"][0]["resource"]).to_equal("http://url1")
    expect(config["rest"][1]["resource"]).to_equal("http://url2")


@test
async def setup_minimum_payload_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test setup with minimum configuration (payload_template)."""

    aioclient_mock.post(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: [
                    {
                        "resource": "http://localhost",
                        "payload_template": '{% set payload = {"data": "value"} %}{{ payload | to_json }}',
                        "method": "POST",
                        "verify_ssl": "false",
                        "timeout": 30,
                        "sensor": [
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor1",
                                "value_template": "{{ value_json.sensor1 }}",
                            },
                            {
                                "unit_of_measurement": UnitOfInformation.MEGABYTES,
                                "name": "sensor2",
                                "value_template": "{{ value_json.sensor2 }}",
                            },
                        ],
                        "binary_sensor": [
                            {
                                "name": "binary_sensor1",
                                "value_template": "{{ value_json.binary_sensor1 }}",
                            },
                            {
                                "name": "binary_sensor2",
                                "value_template": "{{ value_json.binary_sensor2 }}",
                            },
                        ],
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(4)

    expect(hass.states.get("sensor.sensor1").state).to_equal("1")
    expect(hass.states.get("sensor.sensor2").state).to_equal("2")
    expect(hass.states.get("binary_sensor.binary_sensor1").state).to_equal("on")
    expect(hass.states.get("binary_sensor.binary_sensor2").state).to_equal("off")
