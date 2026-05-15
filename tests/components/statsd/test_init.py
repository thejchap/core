"""The tests for the StatsD feeder."""

from collections.abc import Generator
from unittest import mock
from unittest.mock import MagicMock, patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components import statsd
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_client() -> Generator[MagicMock]:
    """Pytest fixture for statsd library."""
    with patch("statsd.StatsClient") as mock_client:
        yield mock_client.return_value


@test
def invalid_config() -> None:
    """Test configuration with defaults."""
    config = {"statsd": {"host1": "host1"}}

    expect(lambda: statsd.CONFIG_SCHEMA(None)).to_raise(vol.Invalid)
    expect(lambda: statsd.CONFIG_SCHEMA(config)).to_raise(vol.Invalid)


@test
async def statsd_setup_full(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup with all data."""
    config = {"statsd": {"host": "host", "port": 123, "rate": 1, "prefix": "foo"}}
    with patch("statsd.StatsClient") as mock_init:
        expect(await async_setup_component(hass, statsd.DOMAIN, config)).to_be(True)

        expect(mock_init.call_count).to_equal(1)
        expect(mock_init.call_args).to_equal(
            mock.call(host="host", port=123, prefix="foo")
        )

        hass.states.async_set("domain.test", "on")
        await hass.async_block_till_done()
        expect(len(mock_init.mock_calls)).to_equal(3)


@test
async def statsd_setup_defaults(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup with defaults."""
    config = {"statsd": {"host": "host"}}

    config["statsd"][statsd.CONF_PORT] = statsd.DEFAULT_PORT
    config["statsd"][statsd.CONF_PREFIX] = statsd.DEFAULT_PREFIX

    with patch("statsd.StatsClient") as mock_init:
        expect(await async_setup_component(hass, statsd.DOMAIN, config)).to_be(True)

        expect(mock_init.call_count).to_equal(1)
        expect(mock_init.call_args).to_equal(
            mock.call(host="host", port=8125, prefix="hass")
        )
        hass.states.async_set("domain.test", "on")
        await hass.async_block_till_done()
        expect(len(mock_init.mock_calls)).to_equal(3)


@test
async def event_listener_defaults(
    hass: HomeAssistant = Depends(hass),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test event listener."""
    config = {"statsd": {"host": "host", "value_mapping": {"custom": 3}}}

    config["statsd"][statsd.CONF_RATE] = statsd.DEFAULT_RATE

    await async_setup_component(hass, statsd.DOMAIN, config)

    valid = {"1": 1, "1.0": 1.0, "custom": 3, STATE_ON: 1, STATE_OFF: 0}
    for in_, out in valid.items():
        hass.states.async_set("domain.test", in_, {"attribute key": 3.2})
        await hass.async_block_till_done()
        mock_client.gauge.assert_has_calls(
            [mock.call("domain.test", out, statsd.DEFAULT_RATE)]
        )

        mock_client.gauge.reset_mock()

        expect(mock_client.incr.call_count).to_equal(1)
        expect(mock_client.incr.call_args).to_equal(
            mock.call("domain.test", rate=statsd.DEFAULT_RATE)
        )
        mock_client.incr.reset_mock()

    for invalid in ("foo", "", object):
        hass.states.async_set("domain.test", invalid, {})
        await hass.async_block_till_done()
        expect(mock_client.gauge.called).to_be(False)
        expect(mock_client.incr.called).to_be(True)


@test
async def event_listener_attr_details(
    hass: HomeAssistant = Depends(hass),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test event listener."""
    config = {"statsd": {"host": "host", "log_attributes": True}}

    config["statsd"][statsd.CONF_RATE] = statsd.DEFAULT_RATE

    await async_setup_component(hass, statsd.DOMAIN, config)

    valid = {"1": 1, "1.0": 1.0, STATE_ON: 1, STATE_OFF: 0}
    for in_, out in valid.items():
        hass.states.async_set("domain.test", in_, {"attribute key": 3.2})
        await hass.async_block_till_done()
        mock_client.gauge.assert_has_calls(
            [
                mock.call("domain.test.state", out, statsd.DEFAULT_RATE),
                mock.call("domain.test.attribute_key", 3.2, statsd.DEFAULT_RATE),
            ]
        )

        mock_client.gauge.reset_mock()

        expect(mock_client.incr.call_count).to_equal(1)
        expect(mock_client.incr.call_args).to_equal(
            mock.call("domain.test", rate=statsd.DEFAULT_RATE)
        )
        mock_client.incr.reset_mock()

    for invalid in ("foo", "", object):
        hass.states.async_set("domain.test", invalid, {})
        await hass.async_block_till_done()
        expect(mock_client.gauge.called).to_be(False)
        expect(mock_client.incr.called).to_be(True)
