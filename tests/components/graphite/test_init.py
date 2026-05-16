"""The tests for the Graphite component."""

import socket
from unittest import mock
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components import graphite
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mock_gf as mock_gf_fx,
    mock_socket as mock_socket_fx,
    mock_time as mock_time_fx,
)

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def setup(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
) -> None:
    """Test setup."""
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    expect(mock_socket.call_count).to_equal(1)
    expect(mock_socket.call_args).to_equal(mock.call(socket.AF_INET, socket.SOCK_STREAM))


@test
async def setup_failure(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
) -> None:
    """Test setup fails due to socket error."""
    mock_socket.return_value.connect.side_effect = OSError
    expect(
        await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})
    ).to_be_falsy()

    expect(mock_socket.call_count).to_equal(1)
    expect(mock_socket.call_args).to_equal(mock.call(socket.AF_INET, socket.SOCK_STREAM))
    expect(mock_socket.return_value.connect.call_count).to_equal(1)


@test
async def full_config(
    hass: HomeAssistant = Depends(hass_fx),
    mock_gf: MagicMock = Depends(mock_gf_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
) -> None:
    """Test setup with full configuration."""
    config = {"graphite": {"host": "foo", "port": 123, "prefix": "me"}}

    expect(await async_setup_component(hass, graphite.DOMAIN, config)).to_be_truthy()
    expect(mock_gf.call_count).to_equal(1)
    expect(mock_gf.call_args).to_equal(mock.call(hass, "foo", 123, "tcp", "me"))
    expect(mock_socket.call_count).to_equal(1)
    expect(mock_socket.call_args).to_equal(mock.call(socket.AF_INET, socket.SOCK_STREAM))


@test
async def full_udp_config(
    hass: HomeAssistant = Depends(hass_fx),
    mock_gf: MagicMock = Depends(mock_gf_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
) -> None:
    """Test setup with full configuration and UDP protocol."""
    config = {
        "graphite": {"host": "foo", "port": 123, "protocol": "udp", "prefix": "me"}
    }

    expect(await async_setup_component(hass, graphite.DOMAIN, config)).to_be_truthy()
    expect(mock_gf.call_count).to_equal(1)
    expect(mock_gf.call_args).to_equal(mock.call(hass, "foo", 123, "udp", "me"))
    expect(mock_socket.call_count).to_equal(0)


@test
async def config_port(
    hass: HomeAssistant = Depends(hass_fx),
    mock_gf: MagicMock = Depends(mock_gf_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
) -> None:
    """Test setup with invalid port."""
    config = {"graphite": {"host": "foo", "port": 2003}}

    expect(await async_setup_component(hass, graphite.DOMAIN, config)).to_be_truthy()
    expect(mock_gf.called).to_be_truthy()
    expect(mock_socket.call_count).to_equal(1)
    expect(mock_socket.call_args).to_equal(mock.call(socket.AF_INET, socket.SOCK_STREAM))


@test
async def start(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
) -> None:
    """Test the start."""
    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_ON)
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call(b"ha.test.entity.state 1.000000 12345")
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)


@test
async def shutdown(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
) -> None:
    """Test the shutdown."""
    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_ON)
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call(b"ha.test.entity.state 1.000000 12345")
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)

    mock_socket.reset_mock()

    await hass.async_stop()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_OFF)
    await hass.async_block_till_done()

    expect(mock_socket.return_value.connect.call_count).to_equal(0)
    expect(mock_socket.return_value.sendall.call_count).to_equal(0)


@test
async def report_attributes(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
) -> None:
    """Test the reporting with attributes."""
    attrs = {"foo": 1, "bar": 2.0, "baz": True, "bat": "NaN"}
    expected = [
        "ha.test.entity.foo 1.000000 12345",
        "ha.test.entity.bar 2.000000 12345",
        "ha.test.entity.baz 1.000000 12345",
        "ha.test.entity.state 1.000000 12345",
    ]

    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_ON, attrs)
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call("\n".join(expected).encode("utf-8"))
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)


@test
async def report_with_string_state(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
) -> None:
    """Test the reporting with strings."""
    expected = [
        "ha.test.entity.foo 1.000000 12345",
        "ha.test.entity.state 1.000000 12345",
    ]

    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "above_horizon", {"foo": 1.0})
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call("\n".join(expected).encode("utf-8"))
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)

    mock_socket.reset_mock()

    hass.states.async_set("test.entity", "not_float")
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(0)
    expect(mock_socket.return_value.sendall.call_count).to_equal(0)
    expect(mock_socket.return_value.send.call_count).to_equal(0)
    expect(mock_socket.return_value.close.call_count).to_equal(0)


@test
async def report_with_binary_state(
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
) -> None:
    """Test the reporting with binary state."""
    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    expected = [
        "ha.test.entity.foo 1.000000 12345",
        "ha.test.entity.state 1.000000 12345",
    ]
    hass.states.async_set("test.entity", STATE_ON, {"foo": 1.0})
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call("\n".join(expected).encode("utf-8"))
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)

    mock_socket.reset_mock()

    expected = [
        "ha.test.entity.foo 1.000000 12345",
        "ha.test.entity.state 0.000000 12345",
    ]
    hass.states.async_set("test.entity", STATE_OFF, {"foo": 1.0})
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(mock_socket.return_value.connect.call_count).to_equal(1)
    expect(mock_socket.return_value.connect.call_args).to_equal(
        mock.call(("localhost", 2003))
    )
    expect(mock_socket.return_value.sendall.call_count).to_equal(1)
    expect(mock_socket.return_value.sendall.call_args).to_equal(
        mock.call("\n".join(expected).encode("utf-8"))
    )
    expect(mock_socket.return_value.send.call_count).to_equal(1)
    expect(mock_socket.return_value.send.call_args).to_equal(mock.call(b"\n"))
    expect(mock_socket.return_value.close.call_count).to_equal(1)


@test.cases(
    test.case("oserror", error=OSError, log_text="Failed to send data to graphite"),
    test.case("gaierror", error=socket.gaierror, log_text="Unable to connect to host"),
    test.case("exception", error=Exception, log_text="Failed to process STATE_CHANGED event"),
)
async def send_to_graphite_errors(
    error: type[BaseException],
    log_text: str,
    hass: HomeAssistant = Depends(hass_fx),
    mock_socket: MagicMock = Depends(mock_socket_fx),
    mock_time: MagicMock = Depends(mock_time_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test the sending with errors."""
    mock_time.return_value = 12345
    expect(await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})).to_be_truthy()
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    mock_socket.return_value.connect.side_effect = error

    hass.states.async_set("test.entity", STATE_ON)
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    expect(log_text in caplog.text).to_be(True)
