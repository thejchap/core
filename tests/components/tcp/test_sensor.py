"""The tests for the TCP sensor platform."""

from collections.abc import Generator
from copy import copy
from unittest.mock import MagicMock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.tcp import common as tcp
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component
from tests.hass_fixtures import hass

TEST_CONFIG = {
    "sensor": {
        "platform": "tcp",
        tcp.CONF_NAME: "test_name",
        tcp.CONF_HOST: "test_host",
        tcp.CONF_PORT: 12345,
        tcp.CONF_TIMEOUT: tcp.DEFAULT_TIMEOUT + 1,
        tcp.CONF_PAYLOAD: "test_payload",
        tcp.CONF_UNIT_OF_MEASUREMENT: "test_unit",
        tcp.CONF_VALUE_TEMPLATE: "{{ '7.' + value }}",
        tcp.CONF_VALUE_ON: "7.on",
        tcp.CONF_BUFFER_SIZE: tcp.DEFAULT_BUFFER_SIZE + 1,
    }
}
SENSOR_TEST_CONFIG = TEST_CONFIG["sensor"]
TEST_ENTITY = "sensor.test_name"

KEYS_AND_DEFAULTS = {
    tcp.CONF_NAME: tcp.DEFAULT_NAME,
    tcp.CONF_TIMEOUT: tcp.DEFAULT_TIMEOUT,
    tcp.CONF_UNIT_OF_MEASUREMENT: None,
    tcp.CONF_VALUE_TEMPLATE: None,
    tcp.CONF_VALUE_ON: None,
    tcp.CONF_BUFFER_SIZE: tcp.DEFAULT_BUFFER_SIZE,
}

socket_test_value = "123"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_select() -> Generator[MagicMock]:
    """Mock select."""
    with patch(
        "homeassistant.components.tcp.entity.select.select",
        return_value=(True, False, False),
    ) as mock_select:
        yield mock_select


@fixture
def mock_socket(
    _mock_select: MagicMock = Depends(mock_select),
) -> Generator[MagicMock]:
    """Mock socket."""
    with patch("homeassistant.components.tcp.entity.socket.socket") as mock_socket:
        socket_instance = mock_socket.return_value.__enter__.return_value
        socket_instance.recv.return_value = socket_test_value.encode()
        yield socket_instance


@fixture
def mock_ssl_context() -> Generator[MagicMock]:
    """Mock select."""
    with patch(
        "homeassistant.components.tcp.entity.ssl.create_default_context",
    ) as mock_ssl_context:
        mock_ssl_context.return_value.wrap_socket.return_value.recv.return_value = (
            socket_test_value + "567"
        ).encode()
        yield mock_ssl_context


@test
async def setup_platform_valid_config(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
) -> None:
    """Check a valid configuration and call add_entities with sensor."""
    with assert_setup_component(1, "sensor"):
        expect(await async_setup_component(hass, "sensor", TEST_CONFIG)).to_be_truthy()
        await hass.async_block_till_done()


@test
async def setup_platform_invalid_config(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
) -> None:
    """Check an invalid configuration."""
    with assert_setup_component(0):
        expect(
            await async_setup_component(
                hass, "sensor", {"sensor": {"platform": "tcp", "porrt": 1234}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()


@test
async def state(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
    mock_select: MagicMock = Depends(mock_select),
) -> None:
    """Return the contents of _state."""
    expect(await async_setup_component(hass, "sensor", TEST_CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("7.123")
    expect(state.attributes["unit_of_measurement"]).to_equal(
        SENSOR_TEST_CONFIG[tcp.CONF_UNIT_OF_MEASUREMENT]
    )
    expect(mock_socket.connect.called).to_be(True)
    expect(mock_socket.connect.call_args).to_equal(
        call((SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"]))
    )
    expect(mock_socket.send.called).to_be(True)
    expect(mock_socket.send.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["payload"].encode())
    )
    expect(mock_select.call_args).to_equal(
        call([mock_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT])
    )
    expect(mock_socket.recv.called).to_be(True)
    expect(mock_socket.recv.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["buffer_size"])
    )


@test
async def config_uses_defaults(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
) -> None:
    """Check if defaults were set."""
    config = copy(SENSOR_TEST_CONFIG)

    for key in KEYS_AND_DEFAULTS:
        del config[key]

    with assert_setup_component(1) as result_config:
        expect(
            await async_setup_component(hass, "sensor", {"sensor": config})
        ).to_be_truthy()
        await hass.async_block_till_done()

    state = hass.states.get("sensor.tcp_sensor")

    expect(state).not_to_be_none()
    expect(state.state).to_equal("123")

    for key, default in KEYS_AND_DEFAULTS.items():
        expect(result_config["sensor"][0].get(key)).to_equal(default)


@test.cases(
    test.case("connect", sock_attr="connect"),
    test.case("send", sock_attr="send"),
)
async def update_socket_error(
    sock_attr: str,
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
) -> None:
    """Test socket errors during update."""
    socket_method = getattr(mock_socket, sock_attr)
    socket_method.side_effect = OSError("Boom")

    expect(await async_setup_component(hass, "sensor", TEST_CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("unknown")


@test
async def update_select_fails(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
    mock_select: MagicMock = Depends(mock_select),
) -> None:
    """Test select fails to return a socket for reading."""
    mock_select.return_value = (False, False, False)

    expect(await async_setup_component(hass, "sensor", TEST_CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("unknown")


@test
async def update_returns_if_template_render_fails(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
) -> None:
    """Return None if rendering the template fails."""
    config = copy(SENSOR_TEST_CONFIG)
    config[tcp.CONF_VALUE_TEMPLATE] = "{{ value / 0 }}"

    expect(
        await async_setup_component(hass, "sensor", {"sensor": config})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("unknown")


@test
async def ssl_state(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
    mock_select: MagicMock = Depends(mock_select),
    mock_ssl_context: MagicMock = Depends(mock_ssl_context),
) -> None:
    """Return the contents of _state, updated over SSL."""
    config = copy(SENSOR_TEST_CONFIG)
    config[tcp.CONF_SSL] = "on"

    expect(
        await async_setup_component(hass, "sensor", {"sensor": config})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("7.123567")
    expect(mock_socket.connect.called).to_be(True)
    expect(mock_socket.connect.call_args).to_equal(
        call((SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"]))
    )
    expect(mock_socket.send.called).to_be(False)
    expect(mock_ssl_context.called).to_be(True)
    expect(bool(mock_ssl_context.return_value.check_hostname)).to_be(True)
    mock_ssl_socket = mock_ssl_context.return_value.wrap_socket.return_value
    expect(mock_ssl_socket.send.called).to_be(True)
    expect(mock_ssl_socket.send.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["payload"].encode())
    )
    expect(mock_select.call_args).to_equal(
        call([mock_ssl_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT])
    )
    expect(mock_ssl_socket.recv.called).to_be(True)
    expect(mock_ssl_socket.recv.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["buffer_size"])
    )


@test
async def ssl_state_verify_off(
    hass: HomeAssistant = Depends(hass),
    mock_socket: MagicMock = Depends(mock_socket),
    mock_select: MagicMock = Depends(mock_select),
    mock_ssl_context: MagicMock = Depends(mock_ssl_context),
) -> None:
    """Return the contents of _state, updated over SSL (verify_ssl disabled)."""
    config = copy(SENSOR_TEST_CONFIG)
    config[tcp.CONF_SSL] = "on"
    config[tcp.CONF_VERIFY_SSL] = "off"

    expect(
        await async_setup_component(hass, "sensor", {"sensor": config})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    expect(state).not_to_be_none()
    expect(state.state).to_equal("7.123567")
    expect(mock_socket.connect.called).to_be(True)
    expect(mock_socket.connect.call_args).to_equal(
        call((SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"]))
    )
    expect(mock_socket.send.called).to_be(False)
    expect(mock_ssl_context.called).to_be(True)
    expect(bool(mock_ssl_context.return_value.check_hostname)).to_be(False)
    mock_ssl_socket = mock_ssl_context.return_value.wrap_socket.return_value
    expect(mock_ssl_socket.send.called).to_be(True)
    expect(mock_ssl_socket.send.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["payload"].encode())
    )
    expect(mock_select.call_args).to_equal(
        call([mock_ssl_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT])
    )
    expect(mock_ssl_socket.recv.called).to_be(True)
    expect(mock_ssl_socket.recv.call_args).to_equal(
        call(SENSOR_TEST_CONFIG["buffer_size"])
    )
