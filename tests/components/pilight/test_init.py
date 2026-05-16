"""The tests for the pilight component."""

from datetime import timedelta
import logging
import socket
from unittest.mock import PropertyMock, patch

from tryke import Depends, expect, fixture, test
from voluptuous import MultipleInvalid

from homeassistant.components import pilight
from homeassistant.core import HomeAssistant
from homeassistant.loader import Integration
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    assert_setup_component,
    async_capture_events,
    async_fire_time_changed,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture."""
    return 0


@fixture
def _enable_pilight():
    """Bypass the manifest 'disabled' flag for the pilight integration."""
    with patch.object(
        Integration,
        "disabled",
        new_callable=PropertyMock,
        return_value=None,
    ):
        yield


class PilightDaemonSim:
    """Class to fake the interface of the pilight python package.

    Is used in an asyncio loop, thus the mock cannot be accessed to
    determine if methods where called?!
    This is solved here in a hackish way by printing errors
    that can be checked using logging.error mocks.
    """

    callback = None
    called = None

    test_message = {
        "protocol": "kaku_switch",
        "uuid": "1-2-3-4",
        "message": {"id": 0, "unit": 0, "off": 1},
    }

    def __init__(self, host, port) -> None:
        """Init pilight client, ignore parameters."""

    def send_code(self, call):
        """Handle pilight.send service callback."""
        _LOGGER.error("PilightDaemonSim payload: %s", call)

    def start(self):
        """Handle homeassistant.start callback.

        Also sends one test message after start up
        """
        _LOGGER.error("PilightDaemonSim start")
        # Fake one code receive after daemon started
        if not self.called:
            self.callback(self.test_message)
            self.called = True

    def stop(self):
        """Handle homeassistant.stop callback."""
        _LOGGER.error("PilightDaemonSim stop")

    def set_callback(self, function):
        """Handle pilight.pilight_received event callback."""
        self.callback = function
        _LOGGER.error("PilightDaemonSim callback: %s", function)


@test
async def connection_failed_error(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to connect at 127.0.0.1:5001 with socket error."""
    with (
        patch("homeassistant.components.pilight._LOGGER.error") as mock_error,
        assert_setup_component(4),
        patch("pilight.pilight.Client", side_effect=socket.error) as mock_client,
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(False)
        mock_client.assert_called_once_with(
            host=pilight.DEFAULT_HOST, port=pilight.DEFAULT_PORT
        )
        expect(mock_error.call_count).to_be(1)


@test
async def connection_timeout_error(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to connect at 127.0.0.1:5001 with socket timeout."""
    with (
        patch("homeassistant.components.pilight._LOGGER.error") as mock_error,
        assert_setup_component(4),
        patch("pilight.pilight.Client", side_effect=socket.timeout) as mock_client,
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(False)
        mock_client.assert_called_once_with(
            host=pilight.DEFAULT_HOST, port=pilight.DEFAULT_PORT
        )
        expect(mock_error.call_count).to_be(1)


@test
async def send_code_no_protocol(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to send data without protocol information, should give error."""
    with (
        patch("pilight.pilight.Client", PilightDaemonSim),
        assert_setup_component(4),
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(True)

        excinfo: list[BaseException] = []
        try:
            await hass.services.async_call(
                pilight.DOMAIN,
                pilight.SERVICE_NAME,
                service_data={"noprotocol": "test", "value": 42},
                blocking=True,
            )
        except MultipleInvalid as err:
            excinfo.append(err)
        expect(len(excinfo)).to_be(1)
        expect("required key not provided @ data['protocol']" in str(excinfo[0])).to_be(
            True
        )


@test
async def send_code(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to send proper data."""
    with (
        patch("pilight.pilight.Client", PilightDaemonSim),
        patch("homeassistant.components.pilight._LOGGER", _LOGGER),
        patch("homeassistant.components.pilight._LOGGER.error") as mock_pilight_error,
        assert_setup_component(4),
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(True)

        service_data = {"protocol": "test", "value": 42}
        await hass.services.async_call(
            pilight.DOMAIN,
            pilight.SERVICE_NAME,
            service_data=service_data,
            blocking=True,
        )
        await hass.async_block_till_done()
        error_log_call = mock_pilight_error.call_args_list[-1]
        service_data["protocol"] = [service_data["protocol"]]
        expect(str(service_data) in str(error_log_call)).to_be(True)


@test
async def send_code_fail(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check IOError exception error message."""
    with (
        patch("pilight.pilight.Client", PilightDaemonSim),
        patch("homeassistant.components.pilight._LOGGER.error") as mock_pilight_error,
        assert_setup_component(4),
        patch("pilight.pilight.Client.send_code", side_effect=IOError),
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(True)

        service_data = {"protocol": "test", "value": 42}
        await hass.services.async_call(
            pilight.DOMAIN,
            pilight.SERVICE_NAME,
            service_data=service_data,
            blocking=True,
        )
        await hass.async_block_till_done()
        error_log_call = mock_pilight_error.call_args_list[-1]
        expect("Pilight send failed" in str(error_log_call)).to_be(True)


@test
async def send_code_delay(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to send proper data with delay afterwards."""
    with (
        patch("pilight.pilight.Client", PilightDaemonSim),
        patch("homeassistant.components.pilight._LOGGER", _LOGGER),
        patch("homeassistant.components.pilight._LOGGER.error") as mock_pilight_error,
        assert_setup_component(4),
    ):
        expect(
            await async_setup_component(
                hass,
                pilight.DOMAIN,
                {pilight.DOMAIN: {pilight.CONF_SEND_DELAY: 5.0}},
            )
        ).to_be(True)

        service_data1 = {"protocol": "test11", "value": 42}
        service_data2 = {"protocol": "test22", "value": 42}
        await hass.services.async_call(
            pilight.DOMAIN,
            pilight.SERVICE_NAME,
            service_data=service_data1,
            blocking=True,
        )
        await hass.services.async_call(
            pilight.DOMAIN,
            pilight.SERVICE_NAME,
            service_data=service_data2,
            blocking=True,
        )
        service_data1["protocol"] = [service_data1["protocol"]]
        service_data2["protocol"] = [service_data2["protocol"]]

        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()
        error_log_call = mock_pilight_error.call_args_list[-1]
        expect(str(service_data1) in str(error_log_call)).to_be(True)

        new_time = dt_util.utcnow() + timedelta(seconds=5)
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()
        error_log_call = mock_pilight_error.call_args_list[-1]
        expect(str(service_data2) in str(error_log_call)).to_be(True)


@test
async def start_stop(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check correct startup and stop of pilight daemon."""
    with (
        patch("pilight.pilight.Client", PilightDaemonSim),
        patch("homeassistant.components.pilight._LOGGER", _LOGGER),
        patch("homeassistant.components.pilight._LOGGER.error") as mock_pilight_error,
        assert_setup_component(4),
    ):
        expect(
            await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
        ).to_be(True)

        await hass.async_start()
        await hass.async_block_till_done()

        error_log_call = mock_pilight_error.call_args_list[-2]
        expect("PilightDaemonSim callback" in str(error_log_call)).to_be(True)
        error_log_call = mock_pilight_error.call_args_list[-1]
        expect("PilightDaemonSim start" in str(error_log_call)).to_be(True)

        with patch.object(hass.loop, "stop"):
            await hass.async_stop()
        error_log_call = mock_pilight_error.call_args_list[-1]
        expect("PilightDaemonSim stop" in str(error_log_call)).to_be(True)


@test
async def receive_code(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check if code receiving via pilight daemon works."""
    with patch("pilight.pilight.Client", PilightDaemonSim):
        events = async_capture_events(hass, pilight.EVENT)
        with assert_setup_component(4):
            expect(
                await async_setup_component(hass, pilight.DOMAIN, {pilight.DOMAIN: {}})
            ).to_be(True)

            await hass.async_start()
            await hass.async_block_till_done()

            expected_message = dict(
                {
                    "protocol": PilightDaemonSim.test_message["protocol"],
                    "uuid": PilightDaemonSim.test_message["uuid"],
                },
                **PilightDaemonSim.test_message["message"],
            )
            expect(events[0].data).to_equal(expected_message)


@test
async def whitelist_exact_match(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check whitelist filter with matched data."""
    with patch("pilight.pilight.Client", PilightDaemonSim):
        events = async_capture_events(hass, pilight.EVENT)
        with assert_setup_component(4):
            whitelist = {
                "protocol": [PilightDaemonSim.test_message["protocol"]],
                "uuid": [PilightDaemonSim.test_message["uuid"]],
                "id": [PilightDaemonSim.test_message["message"]["id"]],
                "unit": [PilightDaemonSim.test_message["message"]["unit"]],
            }
            expect(
                await async_setup_component(
                    hass, pilight.DOMAIN, {pilight.DOMAIN: {"whitelist": whitelist}}
                )
            ).to_be(True)

            await hass.async_start()
            await hass.async_block_till_done()

            expected_message = dict(
                {
                    "protocol": PilightDaemonSim.test_message["protocol"],
                    "uuid": PilightDaemonSim.test_message["uuid"],
                },
                **PilightDaemonSim.test_message["message"],
            )
            expect(events[0].data).to_equal(expected_message)


@test
async def whitelist_partial_match(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check whitelist filter with partially matched data, should work."""
    with patch("pilight.pilight.Client", PilightDaemonSim):
        events = async_capture_events(hass, pilight.EVENT)
        with assert_setup_component(4):
            whitelist = {
                "protocol": [PilightDaemonSim.test_message["protocol"]],
                "id": [PilightDaemonSim.test_message["message"]["id"]],
            }
            expect(
                await async_setup_component(
                    hass, pilight.DOMAIN, {pilight.DOMAIN: {"whitelist": whitelist}}
                )
            ).to_be(True)

            await hass.async_start()
            await hass.async_block_till_done()

            expected_message = dict(
                {
                    "protocol": PilightDaemonSim.test_message["protocol"],
                    "uuid": PilightDaemonSim.test_message["uuid"],
                },
                **PilightDaemonSim.test_message["message"],
            )
            expect(events[0].data).to_equal(expected_message)


@test
async def whitelist_or_match(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check whitelist filter with several subsection, should work."""
    with patch("pilight.pilight.Client", PilightDaemonSim):
        events = async_capture_events(hass, pilight.EVENT)

        with assert_setup_component(4):
            whitelist = {
                "protocol": [
                    PilightDaemonSim.test_message["protocol"],
                    "other_protocol",
                ],
                "id": [PilightDaemonSim.test_message["message"]["id"]],
            }
            expect(
                await async_setup_component(
                    hass, pilight.DOMAIN, {pilight.DOMAIN: {"whitelist": whitelist}}
                )
            ).to_be(True)

            await hass.async_start()
            await hass.async_block_till_done()

            expected_message = dict(
                {
                    "protocol": PilightDaemonSim.test_message["protocol"],
                    "uuid": PilightDaemonSim.test_message["uuid"],
                },
                **PilightDaemonSim.test_message["message"],
            )
            expect(events[0].data).to_equal(expected_message)


@test
async def whitelist_no_match(
    _trigger: int = Depends(_trigger_executor),
    _enable: None = Depends(_enable_pilight),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check whitelist filter with unmatched data, should not work."""
    with patch("pilight.pilight.Client", PilightDaemonSim):
        events = async_capture_events(hass, pilight.EVENT)

        with assert_setup_component(4):
            whitelist = {
                "protocol": ["wrong_protocol"],
                "id": [PilightDaemonSim.test_message["message"]["id"]],
            }
            expect(
                await async_setup_component(
                    hass, pilight.DOMAIN, {pilight.DOMAIN: {"whitelist": whitelist}}
                )
            ).to_be(True)

            await hass.async_start()
            await hass.async_block_till_done()

            expect(len(events)).to_be(0)


@test
async def call_rate_delay_throttle_enabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that throttling actually work."""
    runs: list[int] = []
    delay = 5.0

    limit = pilight.CallRateDelayThrottle(hass, delay)
    # pylint: disable-next=unnecessary-lambda
    action = limit.limited(lambda x: runs.append(x))

    for i in range(3):
        await hass.async_add_executor_job(action, i)

    await hass.async_block_till_done()
    expect(runs).to_equal([0])

    exp: list[int] = []
    now = dt_util.utcnow()
    for i in range(3):
        exp.append(i)
        shifted_time = now + (timedelta(seconds=delay + 0.1) * i)
        async_fire_time_changed(hass, shifted_time)
        await hass.async_block_till_done()
        expect(runs).to_equal(exp)


@test
def call_rate_delay_throttle_disabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the limiter is a noop if no delay set."""
    runs: list[int] = []

    limit = pilight.CallRateDelayThrottle(hass, 0.0)
    # pylint: disable-next=unnecessary-lambda
    action = limit.limited(lambda x: runs.append(x))

    for i in range(3):
        action(i)

    expect(runs).to_equal([0, 1, 2])
