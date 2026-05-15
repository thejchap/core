"""The test for sensor helpers."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor.helpers import async_parse_date_datetime

from tests.hass_fixtures import LogCapture, caplog as caplog_fixture


@fixture
def _caplog_trigger(caplog: LogCapture = Depends(caplog_fixture)) -> LogCapture:
    return caplog


@test.cases(
    test.case("timestamp", device_class=SensorDeviceClass.TIMESTAMP),
    test.case("uptime", device_class=SensorDeviceClass.UPTIME),
)
def async_parse_datetime(
    *,
    device_class: SensorDeviceClass,
    caplog: LogCapture = Depends(_caplog_trigger),
) -> None:
    """Test async_parse_date_datetime."""
    entity_id = "sensor.timestamp"
    expect(
        async_parse_date_datetime(
            "2021-12-12 12:12Z", entity_id, device_class
        ).isoformat()
    ).to_equal("2021-12-12T12:12:00+00:00")
    expect(caplog.text).to_be_falsy()

    expect(
        async_parse_date_datetime("2021-12-12 12:12", entity_id, device_class)
    ).to_be(None)
    expect(
        "sensor.timestamp rendered timestamp without timezone" in caplog.text
    ).to_be(True)

    expect(async_parse_date_datetime("12 past 12", entity_id, device_class)).to_be(
        None
    )
    expect(
        "sensor.timestamp rendered invalid timestamp: 12 past 12" in caplog.text
    ).to_be(True)

    date_class = SensorDeviceClass.DATE
    caplog.clear()
    expect(
        async_parse_date_datetime("2021-12-12", entity_id, date_class).isoformat()
    ).to_equal("2021-12-12")
    expect(caplog.text).to_be_falsy()

    expect(async_parse_date_datetime("December 12th", entity_id, date_class)).to_be(
        None
    )
    expect(
        "sensor.timestamp rendered invalid date December 12th" in caplog.text
    ).to_be(True)
