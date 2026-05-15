"""The tests for the Datadog component."""

from unittest import mock
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.datadog.const import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_PREFIX,
    DEFAULT_RATE,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_LOGBOOK_ENTRY, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .common import MOCK_DATA, MOCK_OPTIONS, create_mock_state

from tests.common import EVENT_STATE_CHANGED, MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def invalid_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid configuration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host1": "host1"},
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(False)


@test
async def datadog_setup_full(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with all data."""
    with patch("homeassistant.components.datadog.DogStatsd") as mock_dogstatsd:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "host",
                "port": 123,
            },
            options={
                "rate": 1,
                "prefix": "foo",
            },
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(mock_dogstatsd.call_count).to_equal(1)
        expect(mock_dogstatsd.call_args).to_equal(
            mock.call(host="host", port=123, namespace="foo", disable_telemetry=True)
        )


@test
async def datadog_setup_defaults(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with defaults."""
    with patch("homeassistant.components.datadog.DogStatsd") as mock_dogstatsd:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=MOCK_DATA,
            options=MOCK_OPTIONS,
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

        expect(mock_dogstatsd.call_count).to_equal(1)
        expect(mock_dogstatsd.call_args).to_equal(
            mock.call(
                host="localhost", port=8125, namespace="hass", disable_telemetry=True
            )
        )


@test
async def logbook_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test event listener."""
    with (
        patch("homeassistant.components.datadog.DogStatsd") as mock_statsd_class,
        patch(
            "homeassistant.components.datadog.config_flow.DogStatsd", mock_statsd_class
        ),
    ):
        mock_statsd = mock_statsd_class.return_value
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": DEFAULT_HOST,
                "port": DEFAULT_PORT,
            },
            options={
                "rate": DEFAULT_RATE,
                "prefix": DEFAULT_PREFIX,
            },
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

        event = {
            "domain": "automation",
            "entity_id": "sensor.foo.bar",
            "message": "foo bar baz",
            "name": "triggered something",
        }
        hass.bus.async_fire(EVENT_LOGBOOK_ENTRY, event)
        await hass.async_block_till_done()

        expect(mock_statsd.event.call_count).to_equal(1)
        expect(mock_statsd.event.call_args).to_equal(
            mock.call(
                title="Home Assistant",
                message=f"%%% \n **{event['name']}** {event['message']} \n %%%",
                tags=["entity:sensor.foo.bar", "domain:automation"],
            )
        )


@test
async def state_changed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test event listener."""
    with (
        patch("homeassistant.components.datadog.DogStatsd") as mock_statsd_class,
        patch(
            "homeassistant.components.datadog.config_flow.DogStatsd", mock_statsd_class
        ),
    ):
        mock_statsd = mock_statsd_class.return_value
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "host",
                "port": DEFAULT_PORT,
            },
            options={"prefix": "ha", "rate": DEFAULT_RATE},
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

        valid = {"1": 1, "1.0": 1.0, STATE_ON: 1, STATE_OFF: 0}

        attributes = {"elevation": 3.2, "temperature": 5.0, "up": True, "down": False}

        for in_, out in valid.items():
            state = create_mock_state("sensor.foobar", in_, attributes)
            hass.states.async_set(state.entity_id, state.state, state.attributes)
            await hass.async_block_till_done()
            expect(mock_statsd.gauge.call_count).to_equal(5)

            for attribute, value in attributes.items():
                value = int(value) if isinstance(value, bool) else value
                mock_statsd.gauge.assert_has_calls(
                    [
                        mock.call(
                            f"ha.sensor.{attribute}",
                            value,
                            sample_rate=1,
                            tags=[f"entity:{state.entity_id}"],
                        )
                    ]
                )

            expect(mock_statsd.gauge.call_args).to_equal(
                mock.call(
                    "ha.sensor",
                    out,
                    sample_rate=1,
                    tags=[f"entity:{state.entity_id}"],
                )
            )

            mock_statsd.gauge.reset_mock()

        for invalid in ("foo", "", object):
            hass.states.async_set("domain.test", invalid, {})
            await hass.async_block_till_done()
            expect(mock_statsd.gauge.called).to_be(False)


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unloading the config entry cleans up properly."""
    client = mock.MagicMock()

    with (
        patch("homeassistant.components.datadog.DogStatsd", return_value=client),
        patch("homeassistant.components.datadog.initialize"),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=MOCK_DATA,
            options=MOCK_OPTIONS,
        )
        entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(entry.state is ConfigEntryState.LOADED).to_be(True)
        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)

    client.flush.assert_called_once()
    client.close_socket.assert_called_once()


@test
async def state_changed_skips_unknown(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state_changed_listener skips None and unknown states."""
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd"
    ) as mock_dogstatsd:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=MOCK_DATA,
            options=MOCK_OPTIONS,
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)

        # Test None state
        hass.bus.async_fire(EVENT_STATE_CHANGED, {"new_state": None})
        await hass.async_block_till_done()
        expect(mock_dogstatsd.gauge.called).to_be(False)

        # Test STATE_UNKNOWN
        unknown_state = mock.MagicMock()
        unknown_state.state = STATE_UNKNOWN
        hass.bus.async_fire(EVENT_STATE_CHANGED, {"new_state": unknown_state})
        await hass.async_block_till_done()
        expect(mock_dogstatsd.gauge.called).to_be(False)
