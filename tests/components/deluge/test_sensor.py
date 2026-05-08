"""Test Deluge sensor.py methods."""

from tryke import expect, test

from homeassistant.components.deluge.const import DelugeSensorType
from homeassistant.components.deluge.sensor import get_state

from . import GET_TORRENT_STATUS_RESPONSE


@test
def get_state_test() -> None:
    """Tests get_state() with different keys."""

    download_result = get_state(
        GET_TORRENT_STATUS_RESPONSE, DelugeSensorType.DOWNLOAD_SPEED_SENSOR
    )
    expect(download_result).to_equal(0.1)  # round(98.5 / 1024, 2)

    upload_result = get_state(
        GET_TORRENT_STATUS_RESPONSE, DelugeSensorType.UPLOAD_SPEED_SENSOR
    )
    expect(upload_result).to_equal(3.4)  # round(3462.0 / 1024, 1)

    protocol_upload_result = get_state(
        GET_TORRENT_STATUS_RESPONSE,
        DelugeSensorType.PROTOCOL_TRAFFIC_UPLOAD_SPEED_SENSOR,
    )
    expect(protocol_upload_result).to_equal(7.6)  # round(7818.0 / 1024, 1)

    protocol_download_result = get_state(
        GET_TORRENT_STATUS_RESPONSE,
        DelugeSensorType.PROTOCOL_TRAFFIC_DOWNLOAD_SPEED_SENSOR,
    )
    expect(protocol_download_result).to_equal(2.6)  # round(2658.0/1024, 1)
