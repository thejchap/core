"""The tests for the Google Wifi platform."""

from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any
from unittest.mock import Mock, patch

import requests_mock as rm_lib
from tryke import Depends, expect, fixture, test

from homeassistant.components.google_wifi import sensor as google_wifi
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    MockEntityPlatform,
    assert_setup_component,
    async_fire_time_changed,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import requests_mock_session

NAME = "foo"

MOCK_DATA = (
    '{"software": {"softwareVersion":"initial",'
    '"updateNewVersion":"initial"},'
    '"system": {"uptime":86400},'
    '"wan": {"localIpAddress":"initial", "online":true,'
    '"ipAddress":true}}'
)

MOCK_DATA_NEXT = (
    '{"software": {"softwareVersion":"next",'
    '"updateNewVersion":"0.0.0.0"},'
    '"system": {"uptime":172800},'
    '"wan": {"localIpAddress":"next", "online":false,'
    '"ipAddress":false}}'
)

MOCK_DATA_MISSING = '{"software": {},"system": {},"wan": {}}'


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture to ensure mock_network is active."""
    return 0


@test
async def setup_minimum(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test setup with minimum configuration."""
    resource = f"http://{google_wifi.DEFAULT_HOST}{google_wifi.ENDPOINT}"
    requests_mock_fx.get(resource, status_code=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {"sensor": {"platform": "google_wifi", "monitored_conditions": ["uptime"]}},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    assert_setup_component(1, "sensor")


@test
async def setup_get(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test setup with full configuration."""
    resource = f"http://localhost{google_wifi.ENDPOINT}"
    requests_mock_fx.get(resource, status_code=HTTPStatus.OK)
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": {
                    "platform": "google_wifi",
                    "host": "localhost",
                    "name": "Test Wifi",
                    "monitored_conditions": [
                        "current_version",
                        "new_version",
                        "uptime",
                        "last_restart",
                        "local_ip",
                        "status",
                    ],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    assert_setup_component(6, "sensor")


def setup_api(
    hass: HomeAssistant | None,
    data: str | None,
    requests_mock_fx: rm_lib.Mocker,
) -> tuple[google_wifi.GoogleWifiAPI, dict[str, Any]]:
    """Set up API with fake data."""
    resource = f"http://localhost{google_wifi.ENDPOINT}"
    now = datetime(1970, month=1, day=1)
    sensor_dict: dict[str, Any] = {}
    with patch("homeassistant.util.dt.now", return_value=now):
        requests_mock_fx.get(resource, text=data, status_code=HTTPStatus.OK)
        conditions = google_wifi.SENSOR_KEYS
        api = google_wifi.GoogleWifiAPI("localhost", conditions)
    for desc in google_wifi.SENSOR_TYPES:
        sensor_dict[desc.key] = {
            "sensor": google_wifi.GoogleWifiSensor(api, NAME, desc),
            "name": f"{NAME}_{desc.key}",
            "units": desc.native_unit_of_measurement,
            "icon": desc.icon,
        }
    for value in sensor_dict.values():
        sensor = value["sensor"]
        sensor.hass = hass

    return api, sensor_dict


def fake_delay(hass: HomeAssistant, ha_delay: int) -> None:
    """Fake delay to prevent update throttle."""
    hass_now = dt_util.utcnow()
    shifted_time = hass_now + timedelta(seconds=ha_delay)
    async_fire_time_changed(hass, shifted_time)


@test
async def name(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test the name."""
    _api, sensor_dict = setup_api(None, MOCK_DATA, requests_mock_fx)
    for value in sensor_dict.values():
        sensor = value["sensor"]
        sensor.platform = MockEntityPlatform(hass)
        test_name = value["name"]
        expect(test_name).to_equal(sensor.name)


@test
async def unit_of_measurement(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test the unit of measurement."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA, requests_mock_fx)
    for value in sensor_dict.values():
        sensor = value["sensor"]
        expect(value["units"]).to_equal(sensor.unit_of_measurement)


@test
async def icon(
    _trigger: int = Depends(_trigger_executor),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test the icon."""
    _api, sensor_dict = setup_api(None, MOCK_DATA, requests_mock_fx)
    for value in sensor_dict.values():
        sensor = value["sensor"]
        expect(value["icon"]).to_equal(sensor.icon)


@test
async def state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test the initial state."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA, requests_mock_fx)
    now = datetime(1970, month=1, day=1)
    with patch("homeassistant.util.dt.now", return_value=now):
        for sensor_name, value in sensor_dict.items():
            sensor = value["sensor"]
            fake_delay(hass, 2)
            sensor.update()
            if sensor_name == google_wifi.ATTR_LAST_RESTART:
                expect(sensor.state).to_equal("1969-12-31 00:00:00")
            elif sensor_name == google_wifi.ATTR_UPTIME:
                expect(sensor.state).to_equal(1)
            elif sensor_name == google_wifi.ATTR_STATUS:
                expect(sensor.state).to_equal("Online")
            else:
                expect(sensor.state).to_equal("initial")


@test
async def update_when_value_is_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test state gets updated to unknown when sensor returns no data."""
    _api, sensor_dict = setup_api(hass, None, requests_mock_fx)
    for value in sensor_dict.values():
        sensor = value["sensor"]
        fake_delay(hass, 2)
        sensor.update()
        expect(sensor.state).to_be(None)


@test
async def update_when_value_changed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test state gets updated when sensor returns a new status."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA_NEXT, requests_mock_fx)
    now = datetime(1970, month=1, day=1)
    with patch("homeassistant.util.dt.now", return_value=now):
        for sensor_name, value in sensor_dict.items():
            sensor = value["sensor"]
            fake_delay(hass, 2)
            sensor.update()
            if sensor_name == google_wifi.ATTR_LAST_RESTART:
                expect(sensor.state).to_equal("1969-12-30 00:00:00")
            elif sensor_name == google_wifi.ATTR_UPTIME:
                expect(sensor.state).to_equal(2)
            elif sensor_name == google_wifi.ATTR_STATUS:
                expect(sensor.state).to_equal("Offline")
            elif sensor_name == google_wifi.ATTR_NEW_VERSION:
                expect(sensor.state).to_equal("Latest")
            elif sensor_name == google_wifi.ATTR_LOCAL_IP:
                expect(sensor.state).to_be_none()
            else:
                expect(sensor.state).to_equal("next")


@test
async def when_api_data_missing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test state logs an error when data is missing."""
    _api, sensor_dict = setup_api(hass, MOCK_DATA_MISSING, requests_mock_fx)
    now = datetime(1970, month=1, day=1)
    with patch("homeassistant.util.dt.now", return_value=now):
        for value in sensor_dict.values():
            sensor = value["sensor"]
            fake_delay(hass, 2)
            sensor.update()
            expect(sensor.state).to_be(None)


def update_side_effect(
    hass: HomeAssistant, requests_mock_fx: rm_lib.Mocker
) -> None:
    """Mock representation of update function."""
    api, _sensor_dict = setup_api(hass, MOCK_DATA, requests_mock_fx)
    api.data = None
    api.available = False


@test
async def update_when_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock_fx: rm_lib.Mocker = Depends(requests_mock_session),
) -> None:
    """Test state updates when Google Wifi unavailable."""
    api, sensor_dict = setup_api(hass, None, requests_mock_fx)
    api.update = Mock(
        "google_wifi.GoogleWifiAPI.update",
        side_effect=update_side_effect(hass, requests_mock_fx),
    )
    for value in sensor_dict.values():
        sensor = value["sensor"]
        sensor.update()
        expect(sensor.state).to_be(None)
