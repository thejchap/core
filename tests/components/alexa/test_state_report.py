"""Test report state."""

import json
from unittest.mock import AsyncMock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import core
from homeassistant.components.alexa import errors, state_report
from homeassistant.components.alexa.resources import AlexaGlobalCatalog
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .test_common import TEST_URL, get_default_config

from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def report_state(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state reports."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa")
    expect(call_json["event"]["header"]["name"]).to_equal("ChangeReport")
    expect(
        call_json["event"]["payload"]["change"]["properties"][0]["value"]
    ).to_equal("NOT_DETECTED")
    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal(
        "binary_sensor#test_contact"
    )


@test
async def report_state_fail(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test proactive state retries once."""
    aioclient_mock.post(
        TEST_URL,
        text=json.dumps(
            {
                "payload": {
                    "code": "THROTTLING_EXCEPTION",
                    "description": "Request could not be processed due to throttling",
                }
            }
        ),
        status=403,
    )

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    # No retry on errors not related to expired access token
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    # Check we log the entity id of the failing entity
    expect(
        "Error when sending ChangeReport for binary_sensor.test_contact to Alexa: "
        "THROTTLING_EXCEPTION: Request could not be processed due to throttling"
        in caplog.text
    ).to_be_truthy()


@test
async def report_state_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test proactive state retries once."""
    aioclient_mock.post(
        TEST_URL,
        exc=aiohttp.ClientError(),
    )

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    # No retry on errors not related to expired access token
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    # Check we log the entity id of the failing entity
    expect(
        "Timeout sending report to Alexa for binary_sensor.test_contact"
        in caplog.text
    ).to_be_truthy()


@test
async def report_state_retry(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state retries once."""
    aioclient_mock.post(
        TEST_URL,
        text='{"payload":{"code":"INVALID_ACCESS_TOKEN_EXCEPTION","description":""}}',
        status=403,
    )

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(2)


@test
async def report_state_unsets_authorized_on_error(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state unsets authorized on error."""
    aioclient_mock.post(
        TEST_URL,
        text='{"payload":{"code":"INVALID_ACCESS_TOKEN_EXCEPTION","description":""}}',
        status=403,
    )

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    config = get_default_config(hass)
    await state_report.async_enable_proactive_mode(hass, config)

    config._store.set_authorized.assert_not_called()

    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    # To trigger event listener
    await hass.async_block_till_done()
    config._store.set_authorized.assert_called_once_with(False)


@test.cases(
    test.case("NoTokenAvailable", exc=errors.NoTokenAvailable),
    test.case("RequireRelink", exc=errors.RequireRelink),
)
async def report_state_unsets_authorized_on_access_token_error(
    exc: type[Exception],
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state unsets authorized on error."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    config = get_default_config(hass)

    await state_report.async_enable_proactive_mode(hass, config)

    config._store.set_authorized.assert_not_called()

    with patch.object(config, "async_get_access_token", AsyncMock(side_effect=exc)):
        hass.states.async_set(
            "binary_sensor.test_contact",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )

        # To trigger event listener
        await hass.async_block_till_done()
        config._store.set_authorized.assert_called_once_with(False)


@test
async def report_state_fan(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state reports with fan instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "fan.test_fan",
        "off",
        {
            "friendly_name": "Test fan",
            "supported_features": 15,
            "oscillating": False,
            "preset_mode": None,
            "preset_modes": ["auto", "smart"],
            "percentage": None,
        },
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "fan.test_fan",
        "on",
        {
            "friendly_name": "Test fan",
            "supported_features": 15,
            "oscillating": True,
            "preset_mode": "smart",
            "preset_modes": ["auto", "smart"],
            "percentage": 90,
        },
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa")
    expect(call_json["event"]["header"]["name"]).to_equal("ChangeReport")

    change_reports = call_json["event"]["payload"]["change"]["properties"]

    checks = 0
    for report in change_reports:
        if report["name"] == "toggleState":
            expect(report["value"]).to_equal("ON")
            expect(report["instance"]).to_equal("fan.oscillating")
            expect(report["namespace"]).to_equal("Alexa.ToggleController")
            checks += 1
        if report["name"] == "mode":
            expect(report["value"]).to_equal("preset_mode.smart")
            expect(report["instance"]).to_equal("fan.preset_mode")
            expect(report["namespace"]).to_equal("Alexa.ModeController")
            checks += 1
        if report["name"] == "rangeValue":
            expect(report["value"]).to_equal(90)
            expect(report["instance"]).to_equal("fan.percentage")
            expect(report["namespace"]).to_equal("Alexa.RangeController")
            checks += 1
    expect(checks).to_equal(3)

    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal("fan#test_fan")


@test
async def report_state_humidifier(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state reports with humidifier instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "humidifier.test_humidifier",
        "off",
        {
            "friendly_name": "Test humidifier",
            "supported_features": 1,
            "mode": None,
            "available_modes": ["auto", "smart"],
        },
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "humidifier.test_humidifier",
        "on",
        {
            "friendly_name": "Test humidifier",
            "supported_features": 1,
            "mode": "smart",
            "available_modes": ["auto", "smart"],
            "humidity": 55,
        },
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa")
    expect(call_json["event"]["header"]["name"]).to_equal("ChangeReport")

    change_reports = call_json["event"]["payload"]["change"]["properties"]

    checks = 0
    for report in change_reports:
        if report["name"] == "mode":
            expect(report["value"]).to_equal("mode.smart")
            expect(report["instance"]).to_equal("humidifier.mode")
            expect(report["namespace"]).to_equal("Alexa.ModeController")
            checks += 1
        if report["name"] == "rangeValue":
            expect(report["value"]).to_equal(55)
            expect(report["instance"]).to_equal("humidifier.humidity")
            expect(report["namespace"]).to_equal("Alexa.RangeController")
            checks += 1
    expect(checks).to_equal(2)

    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal(
        "humidifier#test_humidifier"
    )


@test.cases(
    test.case(
        "number_no_unit",
        domain="number",
        value=50,
        unit=None,
        label=AlexaGlobalCatalog.SETTING_PRESET,
    ),
    test.case(
        "input_number_meters",
        domain="input_number",
        value=40,
        unit=UnitOfLength.METERS,
        label=AlexaGlobalCatalog.UNIT_DISTANCE_METERS,
    ),
    test.case(
        "number_celsius",
        domain="number",
        value=20.5,
        unit=UnitOfTemperature.CELSIUS,
        label=AlexaGlobalCatalog.UNIT_TEMPERATURE_CELSIUS,
    ),
    test.case(
        "input_number_millimeters",
        domain="input_number",
        value=40.5,
        unit=UnitOfLength.MILLIMETERS,
        label=AlexaGlobalCatalog.SETTING_PRESET,
    ),
    test.case(
        "number_percent",
        domain="number",
        value=20.5,
        unit=PERCENTAGE,
        label=AlexaGlobalCatalog.UNIT_PERCENT,
    ),
)
async def report_state_number(
    domain: str,
    value: float,
    unit: str | None,
    label: AlexaGlobalCatalog,
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test proactive state reports with number or input_number instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)
    state = {
        "friendly_name": f"Test {domain}",
        "min": 10,
        "max": 100,
        "step": 0.1,
    }

    if unit:
        state["unit_of_measurement"] = unit

    hass.states.async_set(
        f"{domain}.test_{domain}",
        None,
        state,
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        f"{domain}.test_{domain}",
        value,
        state,
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa")
    expect(call_json["event"]["header"]["name"]).to_equal("ChangeReport")

    change_reports = call_json["event"]["payload"]["change"]["properties"]

    checks = 0
    for report in change_reports:
        if report["name"] == "connectivity":
            expect(report["value"]).to_equal({"value": "OK"})
            expect(report["namespace"]).to_equal("Alexa.EndpointHealth")
            checks += 1
        if report["name"] == "rangeValue":
            expect(report["value"]).to_equal(value)
            expect(report["instance"]).to_equal(f"{domain}.value")
            expect(report["namespace"]).to_equal("Alexa.RangeController")
            checks += 1
    expect(checks).to_equal(2)

    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal(
        f"{domain}#test_{domain}"
    )


@test
async def send_add_or_update_message(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test sending an AddOrUpdateReport message."""
    aioclient_mock.post(TEST_URL, text="")

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    hass.states.async_set(
        "zwave.bla",
        "wow_such_unsupported",
    )

    entities = [
        "binary_sensor.test_contact",
        "binary_sensor.non_existing",  # Supported, but does not exist
        "zwave.bla",  # Unsupported
    ]
    await state_report.async_send_add_or_update_message(
        hass, get_default_config(hass), entities
    )

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa.Discovery")
    expect(call_json["event"]["header"]["name"]).to_equal("AddOrUpdateReport")
    expect(len(call_json["event"]["payload"]["endpoints"])).to_equal(1)
    expect(call_json["event"]["payload"]["endpoints"][0]["endpointId"]).to_equal(
        "binary_sensor#test_contact"
    )


@test
async def send_delete_message(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test sending an AddOrUpdateReport message."""
    aioclient_mock.post(TEST_URL, json={"data": "is irrelevant"})

    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    await state_report.async_send_delete_message(
        hass, get_default_config(hass), ["binary_sensor.test_contact", "zwave.bla"]
    )

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal("Alexa.Discovery")
    expect(call_json["event"]["header"]["name"]).to_equal("DeleteReport")
    expect(len(call_json["event"]["payload"]["endpoints"])).to_equal(1)
    expect(call_json["event"]["payload"]["endpoints"][0]["endpointId"]).to_equal(
        "binary_sensor#test_contact"
    )


@test
async def doorbell_event(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test doorbell press reports."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "off",
        {
            "friendly_name": "Test Doorbell Sensor",
            "device_class": "occupancy",
            "linkquality": 42,
        },
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {
            "friendly_name": "Test Doorbell Sensor",
            "device_class": "occupancy",
            "linkquality": 42,
        },
    )

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {
            "friendly_name": "Test Doorbell Sensor",
            "device_class": "occupancy",
            "linkquality": 99,
        },
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal(
        "Alexa.DoorbellEventSource"
    )
    expect(call_json["event"]["header"]["name"]).to_equal("DoorbellPress")
    expect(call_json["event"]["payload"]["cause"]["type"]).to_equal(
        "PHYSICAL_INTERACTION"
    )
    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal(
        "binary_sensor#test_doorbell"
    )

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "off",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(2)


@test
async def doorbell_event_from_unknown(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test doorbell press reports."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {
            "friendly_name": "Test Doorbell Sensor",
            "device_class": "occupancy",
        },
    )

    # To trigger event listener
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    expect(call_json["event"]["header"]["namespace"]).to_equal(
        "Alexa.DoorbellEventSource"
    )
    expect(call_json["event"]["header"]["name"]).to_equal("DoorbellPress")
    expect(call_json["event"]["payload"]["cause"]["type"]).to_equal(
        "PHYSICAL_INTERACTION"
    )
    expect(call_json["event"]["endpoint"]["endpointId"]).to_equal(
        "binary_sensor#test_doorbell"
    )


@test
async def doorbell_event_fail(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test proactive state retries once."""
    aioclient_mock.post(
        TEST_URL,
        text=json.dumps(
            {
                "payload": {
                    "code": "THROTTLING_EXCEPTION",
                    "description": "Request could not be processed due to throttling",
                }
            }
        ),
        status=403,
    )

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "off",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    # No retry on errors not related to expired access token
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    # Check we log the entity id of the failing entity
    expect(
        "Error when sending DoorbellPress event for binary_sensor.test_doorbell"
        " to Alexa: THROTTLING_EXCEPTION: Request could not be processed"
        " due to throttling"
        in caplog.text
    ).to_be_truthy()


@test
async def doorbell_event_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test proactive state retries once."""
    aioclient_mock.post(
        TEST_URL,
        exc=aiohttp.ClientError(),
    )

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "off",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "binary_sensor.test_doorbell",
        "on",
        {"friendly_name": "Test Doorbell Sensor", "device_class": "occupancy"},
    )

    # To trigger event listener
    await hass.async_block_till_done()

    # No retry on errors not related to expired access token
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    # Check we log the entity id of the failing entity
    expect(
        "Timeout sending report to Alexa for binary_sensor.test_doorbell"
        in caplog.text
    ).to_be_truthy()


@test
async def proactive_mode_filter_states(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test all the cases that filter states."""
    aioclient_mock.post(TEST_URL, text="", status=202)
    config = get_default_config(hass)
    await state_report.async_enable_proactive_mode(hass, config)

    # First state should report
    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )
    await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    aioclient_mock.clear_requests()

    # Second one shouldn't
    hass.states.async_set(
        "binary_sensor.test_contact",
        "on",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )
    expect(len(aioclient_mock.mock_calls)).to_equal(0)

    # hass not running should not report
    current_state = hass.state
    hass.set_state(core.CoreState.stopping)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    hass.states.async_set(
        "binary_sensor.test_contact",
        "off",
        {"friendly_name": "Test Contact Sensor", "device_class": "door"},
    )

    hass.set_state(current_state)
    expect(len(aioclient_mock.mock_calls)).to_equal(0)

    # unsupported entity should not report
    with patch.dict(
        "homeassistant.components.alexa.state_report.ENTITY_ADAPTERS", {}, clear=True
    ):
        hass.states.async_set(
            "binary_sensor.test_contact",
            "on",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(0)

    # Not exposed by config should not report
    with patch.object(config, "should_expose", return_value=False):
        hass.states.async_set(
            "binary_sensor.test_contact",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(0)

    # Removing an entity
    hass.states.async_remove("binary_sensor.test_contact")
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(0)

    # If serializes to same properties, it should not report
    aioclient_mock.post(TEST_URL, text="", status=202)
    with patch(
        "homeassistant.components.alexa.entities.AlexaEntity.serialize_properties",
        return_value=[{"same": "info"}],
    ):
        hass.states.async_set(
            "binary_sensor.same_serialize",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )
        await hass.async_block_till_done()
        hass.states.async_set(
            "binary_sensor.same_serialize",
            "off",
            {"friendly_name": "Test Contact Sensor", "device_class": "door"},
        )

        await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(1)
