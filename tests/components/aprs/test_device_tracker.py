"""Test APRS device tracker."""

from unittest.mock import Mock, patch

import aprslib
from aprslib import IS
from tryke import Depends, expect, fixture, test

from homeassistant.components.aprs import device_tracker
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture

DEFAULT_PORT = 14580

TEST_CALLSIGN = "testcall"
TEST_COORDS_NULL_ISLAND = (0, 0)
TEST_FILTER = "testfilter"
TEST_HOST = "testhost"
TEST_PASSWORD = "testpass"


@fixture
def _trigger_executor() -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
def make_filter() -> None:
    """Test filter."""
    callsigns = ["CALLSIGN1", "callsign2"]
    res = device_tracker.make_filter(callsigns)
    expect(res).to_equal("b/CALLSIGN1 b/CALLSIGN2")


@test
def gps_accuracy_0() -> None:
    """Test GPS accuracy level 0."""
    acc = device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, 0)
    expect(acc).to_equal(0)


@test
def gps_accuracy_1() -> None:
    """Test GPS accuracy level 1."""
    acc = device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, 1)
    expect(acc).to_equal(186)


@test
def gps_accuracy_2() -> None:
    """Test GPS accuracy level 2."""
    acc = device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, 2)
    expect(acc).to_equal(1855)


@test
def gps_accuracy_3() -> None:
    """Test GPS accuracy level 3."""
    acc = device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, 3)
    expect(acc).to_equal(18553)


@test
def gps_accuracy_4() -> None:
    """Test GPS accuracy level 4."""
    acc = device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, 4)
    expect(acc).to_equal(111319)


@test
def gps_accuracy_invalid_int() -> None:
    """Test GPS accuracy with invalid input."""
    level = 5
    expect(
        lambda: device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, level)
    ).to_raise(ValueError)


@test
def gps_accuracy_invalid_string() -> None:
    """Test GPS accuracy with invalid input."""
    level = "not an int"
    expect(
        lambda: device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, level)
    ).to_raise(ValueError)


@test
def gps_accuracy_invalid_float() -> None:
    """Test GPS accuracy with invalid input."""
    level = 1.2
    expect(
        lambda: device_tracker.gps_accuracy(TEST_COORDS_NULL_ISLAND, level)
    ).to_raise(ValueError)


@test
def aprs_listener() -> None:
    """Test listener thread."""
    with patch("aprslib.IS") as mock_ais:
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        port = DEFAULT_PORT
        see = Mock()

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_truthy()
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        mock_ais.assert_called_with(callsign, passwd=password, host=host, port=port)


@test
def aprs_listener_start_fail() -> None:
    """Test listener thread start failure."""
    with patch.object(
        IS, "connect", side_effect=aprslib.ConnectionError("Unable to connect.")
    ):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_falsy()
        expect(listener.start_message).to_equal("Unable to connect.")


@test
def aprs_listener_stop() -> None:
    """Test listener thread stop."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.ais.close = Mock()
        listener.run()
        listener.stop()

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        expect(listener.start_success).to_be_truthy()
        listener.ais.close.assert_called_with()


@test
def aprs_listener_rx_msg() -> None:
    """Test rx_msg."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        sample_msg = {
            device_tracker.ATTR_FORMAT: "uncompressed",
            device_tracker.ATTR_FROM: "ZZ0FOOBAR-1",
            device_tracker.ATTR_LATITUDE: 0.0,
            device_tracker.ATTR_LONGITUDE: 0.0,
            device_tracker.ATTR_ALTITUDE: 0,
        }

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()
        listener.rx_msg(sample_msg)

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_truthy()
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        see.assert_called_with(
            dev_id=device_tracker.slugify("ZZ0FOOBAR-1"),
            gps=(0.0, 0.0),
            attributes={"altitude": 0},
        )


@test
def aprs_listener_rx_msg_ambiguity() -> None:
    """Test rx_msg with posambiguity."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        sample_msg = {
            device_tracker.ATTR_FORMAT: "uncompressed",
            device_tracker.ATTR_FROM: "ZZ0FOOBAR-1",
            device_tracker.ATTR_LATITUDE: 0.0,
            device_tracker.ATTR_LONGITUDE: 0.0,
            device_tracker.ATTR_POS_AMBIGUITY: 1,
        }

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()
        listener.rx_msg(sample_msg)

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_truthy()
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        see.assert_called_with(
            dev_id=device_tracker.slugify("ZZ0FOOBAR-1"),
            gps=(0.0, 0.0),
            attributes={device_tracker.ATTR_GPS_ACCURACY: 186},
        )


@test
def aprs_listener_rx_msg_ambiguity_invalid() -> None:
    """Test rx_msg with invalid posambiguity."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        sample_msg = {
            device_tracker.ATTR_FORMAT: "uncompressed",
            device_tracker.ATTR_FROM: "ZZ0FOOBAR-1",
            device_tracker.ATTR_LATITUDE: 0.0,
            device_tracker.ATTR_LONGITUDE: 0.0,
            device_tracker.ATTR_POS_AMBIGUITY: 5,
        }

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()
        listener.rx_msg(sample_msg)

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_truthy()
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        see.assert_called_with(
            dev_id=device_tracker.slugify("ZZ0FOOBAR-1"), gps=(0.0, 0.0), attributes={}
        )


@test
def aprs_listener_rx_msg_no_position() -> None:
    """Test rx_msg with non-position report."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        sample_msg = {device_tracker.ATTR_FORMAT: "invalid"}

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()
        listener.rx_msg(sample_msg)

        expect(listener.callsign).to_equal(callsign)
        expect(listener.host).to_equal(host)
        expect(listener.server_filter).to_equal(server_filter)
        expect(listener.see).to_be(see)
        expect(listener.start_event.is_set()).to_be(True)
        expect(listener.start_success).to_be_truthy()
        expect(listener.start_message).to_equal(
            "Connected to testhost with callsign testcall."
        )
        see.assert_not_called()


@test
def aprs_listener_rx_msg_object() -> None:
    """Test rx_msg with object."""
    with patch("aprslib.IS"):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
        see = Mock()

        sample_msg = aprslib.parse(
            "CEEWO2-14>APLWS2,qAU,CEEWO2-15:;V4310251 *121203h5105.72N/00131.89WO085/024/A=033178!w&,!Clb=3.5m/s calibration 21% 404.40MHz Type=RS41 batt=2.7V Details on http://radiosondy.info/"
        )

        listener = device_tracker.AprsListenerThread(
            callsign, password, host, server_filter, see
        )
        listener.run()
        listener.rx_msg(sample_msg)

        see.assert_called_with(
            dev_id=device_tracker.slugify("V4310251"),
            gps=(51.09534249084249, -1.5315201465201465),
            attributes={
                "gps_accuracy": 0,
                "altitude": 10112.654400000001,
                "comment": "Clb=3.5m/s calibration 21% 404.40MHz Type=RS41 batt=2.7V Details on http://radiosondy.info/",
                "course": 85,
                "speed": 44.448,
            },
        )


@test
async def setup_scanner(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup_scanner."""
    with patch(
        "homeassistant.components.aprs.device_tracker.AprsListenerThread"
    ) as listener:
        config = {
            "username": TEST_CALLSIGN,
            "password": TEST_PASSWORD,
            "host": TEST_HOST,
            "callsigns": ["XX0FOO*", "YY0BAR-1"],
            "timeout": device_tracker.DEFAULT_TIMEOUT,
        }

        see = Mock()
        res = await hass.async_add_executor_job(
            device_tracker.setup_scanner, hass, config, see
        )

        expect(res).to_be_truthy()
        listener.assert_called_with(
            TEST_CALLSIGN, TEST_PASSWORD, TEST_HOST, "b/XX0FOO* b/YY0BAR-1", see
        )


@test
async def setup_scanner_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup_scanner failure from timeout."""
    with patch.object(IS, "connect", side_effect=TimeoutError):
        config = {
            "username": TEST_CALLSIGN,
            "password": TEST_PASSWORD,
            "host": "localhost",
            "timeout": 0.01,
            "callsigns": ["XX0FOO*", "YY0BAR-1"],
        }

        see = Mock()
        expect(
            await hass.async_add_executor_job(
                device_tracker.setup_scanner, hass, config, see
            )
        ).to_be_falsy()
