"""Test REST data module logging improvements."""

from datetime import timedelta
import logging
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.rest import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor() -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@test
async def rest_data_log_warning_on_error_status(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that warning is logged for error status codes."""
    aioclient_mock.get(
        "http://example.com/api",
        status=403,
        text="<html><body>Access Denied</body></html>",
        headers={"Content-Type": "text/html"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.test }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).to_contain(
        "REST request to http://example.com/api returned status 403 "
        "with text/html response"
    )
    expect(caplog.text).to_contain("<html><body>Access Denied</body></html>")


@test
async def rest_data_no_warning_on_200_with_wrong_content_type(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that no warning is logged for 200 status with wrong content."""
    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        text="<p>This is HTML, not JSON!</p>",
        headers={"Content-Type": "text/html; charset=utf-8"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).not_.to_contain(
        "REST request to http://example.com/api returned status 200"
    )


@test
async def rest_data_with_incorrect_charset_in_header(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test that we can handle sites which provides an incorrect charset."""
    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        text="<p>Some html</p>",
        headers={"Content-Type": "text/html; charset=utf-8"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "encoding": "windows-1250",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    with patch(
        "tests.test_util.aiohttp.AiohttpClientMockResponse.text",
        side_effect=UnicodeDecodeError("utf-8", b"", 1, 0, ""),
    ):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    log_text = "Response charset came back as utf-8 but could not be decoded, continue with configured encoding windows-1250."
    expect(caplog.text).to_contain(log_text)

    caplog.clear()
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(caplog.text).not_.to_contain(log_text)


@test
async def rest_data_no_warning_on_success_json(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that no warning is logged for successful JSON responses."""
    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        json={"status": "ok", "value": 42},
        headers={"Content-Type": "application/json"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.value }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).not_.to_contain(
        "REST request to http://example.com/api returned status"
    )


@test
async def rest_data_no_warning_on_success_xml(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that no warning is logged for successful XML responses."""
    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        text='<?xml version="1.0"?><root><value>42</value></root>',
        headers={"Content-Type": "application/xml"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.root.value }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).not_.to_contain(
        "REST request to http://example.com/api returned status"
    )


@test
async def rest_data_warning_truncates_long_responses(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that warning truncates very long response bodies."""
    long_message = "Error: " + "x" * 1000

    aioclient_mock.get(
        "http://example.com/api",
        status=500,
        text=long_message,
        headers={"Content-Type": "text/plain"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.test }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    caplog.set_level(logging.WARNING, logger="homeassistant.components.rest.data")

    expect(caplog.text).to_contain(
        "REST request to http://example.com/api returned status 500 "
        "with text/plain response: Error: " + "x" * 493 + "..."
    )


@test
async def rest_data_debug_logging_shows_response_details(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that debug logging shows response details."""
    caplog.set_level(logging.DEBUG)

    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        json={"test": "data"},
        headers={"Content-Type": "application/json"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.test }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).to_contain(
        "REST response from http://example.com/api: status=200, "
        "content-type=application/json, length="
    )


@test
async def rest_data_no_content_type_header(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of responses without Content-Type header."""
    caplog.set_level(logging.DEBUG)

    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        text="plain text response",
        headers={},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).to_contain("content-type=not set")
    expect(caplog.text).not_.to_contain(
        "REST request to http://example.com/api returned status"
    )


@test
async def rest_data_real_world_bom_blocking_scenario(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test real-world scenario where BOM blocks with HTML response."""
    bom_block_html = "<p>Your access is blocked due to automated access</p>"

    aioclient_mock.get(
        "http://www.bom.gov.au/fwo/IDN60901/IDN60901.94767.json",
        status=403,
        text=bom_block_html,
        headers={"Content-Type": "text/html"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": (
                        "http://www.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"
                    ),
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "bom_temperature",
                            "value_template": (
                                "{{ value_json.observations.data[0].air_temp }}"
                            ),
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).to_contain(
        "REST request to http://www.bom.gov.au/fwo/IDN60901/"
        "IDN60901.94767.json returned status 403 with text/html response"
    )
    expect(caplog.text).to_contain("Your access is blocked")


@test
async def rest_data_warning_on_html_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that warning is logged for error status with HTML content."""
    aioclient_mock.get(
        "http://example.com/api",
        status=404,
        text="<html><body><h1>404 Not Found</h1></body></html>",
        headers={"Content-Type": "text/html"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.test }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).to_contain(
        "REST request to http://example.com/api returned status 404 "
        "with text/html response"
    )
    expect(caplog.text).to_contain("<html><body><h1>404 Not Found</h1></body></html>")


@test
async def rest_data_no_warning_on_json_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test POST request that returns JSON error - no warning expected."""
    aioclient_mock.post(
        "http://example.com/api",
        status=400,
        text='{"error": "Invalid request payload"}',
        headers={"Content-Type": "application/json"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "POST",
                    "payload": '{"data": "test"}',
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.error }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(caplog.text).not_.to_contain(
        "REST request to http://example.com/api returned status 400"
    )


@test
async def rest_data_timeout_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test timeout error logging."""
    aioclient_mock.get(
        "http://example.com/api",
        exc=TimeoutError(),
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "timeout": 10,
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.test }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        "Timeout while fetching data: http://example.com/api" in caplog.text
        or "Platform rest not ready yet" in caplog.text
    ).to_be_truthy()


@test
async def rest_data_boolean_params_converted_to_strings(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that boolean parameters are converted to lowercase strings."""
    aioclient_mock.get(
        "http://example.com/api",
        status=200,
        json={"status": "ok"},
        headers={"Content-Type": "application/json"},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "resource": "http://example.com/api",
                    "method": "GET",
                    "params": {
                        "boolTrue": True,
                        "boolFalse": False,
                        "stringParam": "test",
                        "intParam": 123,
                    },
                    "sensor": [
                        {
                            "name": "test_sensor",
                            "value_template": "{{ value_json.status }}",
                        }
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    _method, url, _data, _headers = aioclient_mock.mock_calls[0]

    expect(url.query["boolTrue"]).to_equal("true")
    expect(url.query["boolFalse"]).to_equal("false")
    expect(url.query["stringParam"]).to_equal("test")
    expect(url.query["intParam"]).to_equal("123")
