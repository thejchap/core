"""The tests for the nx584 sensor platform."""

from typing import Any
from unittest import mock

from nx584 import client as nx584_client
import requests
from tryke import Depends, expect, fixture, test

from homeassistant.components.nx584 import binary_sensor as nx584
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import client as client_fx, fake_zones as fake_zones_fx

from tests.hass_fixtures import hass as hass_fx, mock_network

DEFAULT_CONFIG = {
    "host": nx584.DEFAULT_HOST,
    "port": nx584.DEFAULT_PORT,
    "exclude_zones": [],
    "zone_types": {},
}


class StopMe(Exception):
    """Stop helper."""


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
def nx584_sensor_setup_defaults(
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
    fake_zones: list[dict] = Depends(fake_zones_fx),
) -> None:
    """Test the setup with no configuration."""
    with (
        mock.patch(
            "homeassistant.components.nx584.binary_sensor.NX584Watcher"
        ) as _mock_watcher,
        mock.patch(
            "homeassistant.components.nx584.binary_sensor.NX584ZoneSensor"
        ) as mock_nx,
    ):
        add_entities = mock.MagicMock()
        config = DEFAULT_CONFIG
        nx584.setup_platform(hass, config, add_entities)
        mock_nx.assert_has_calls([mock.call(zone, "opening") for zone in fake_zones])
        expect(add_entities.called).to_be_truthy()
        expect(nx584_client.Client.call_count).to_equal(1)
        expect(nx584_client.Client.call_args).to_equal(
            mock.call("http://localhost:5007")
        )


@test
def nx584_sensor_setup_full_config(
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
    fake_zones: list[dict] = Depends(fake_zones_fx),
) -> None:
    """Test the setup with full configuration."""
    with (
        mock.patch(
            "homeassistant.components.nx584.binary_sensor.NX584Watcher"
        ) as mock_watcher,
        mock.patch(
            "homeassistant.components.nx584.binary_sensor.NX584ZoneSensor"
        ) as mock_nx,
    ):
        config = {
            "host": "foo",
            "port": 123,
            "exclude_zones": [2],
            "zone_types": {3: "motion"},
        }
        add_entities = mock.MagicMock()
        nx584.setup_platform(hass, config, add_entities)
        mock_nx.assert_has_calls(
            [
                mock.call(fake_zones[0], "opening"),
                mock.call(fake_zones[2], "motion"),
            ]
        )
        expect(add_entities.called).to_be_truthy()
        expect(nx584_client.Client.call_count).to_equal(1)
        expect(nx584_client.Client.call_args).to_equal(mock.call("http://foo:123"))
        expect(mock_watcher.called).to_be_truthy()


async def _assert_graceful_fail(
    hass: HomeAssistant, config: dict[str, Any]
) -> None:
    """Test the failing."""
    expect(await async_setup_component(hass, "nx584", config)).to_be_falsy()


@test.cases(
    test.case("exclude_zones_str", config={"exclude_zones": ["a"]}),
    test.case("zone_types_bad_key", config={"zone_types": {"a": "b"}}),
    test.case("zone_types_bad_type", config={"zone_types": {1: "notatype"}}),
    test.case("zone_types_bad_zone", config={"zone_types": {"notazone": "motion"}}),
)
async def nx584_sensor_setup_bad_config(
    config: dict[str, Any],
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test the setup with bad configuration."""
    await _assert_graceful_fail(hass, config)


@test.cases(
    test.case("connect_failed", exception_type=requests.exceptions.ConnectionError),
    test.case("no_partitions", exception_type=IndexError),
)
async def nx584_sensor_setup_with_exceptions(
    exception_type: type[Exception],
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test the setup handles exceptions."""
    nx584_client.Client.return_value.list_zones.side_effect = exception_type
    await _assert_graceful_fail(hass, {})


@test
async def nx584_sensor_setup_version_too_old(
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if version is too old."""
    nx584_client.Client.return_value.get_version.return_value = "1.0"
    await _assert_graceful_fail(hass, {})


@test
def nx584_sensor_setup_no_zones(
    _client: mock.MagicMock = Depends(client_fx),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test the setup with no zones."""
    nx584_client.Client.return_value.list_zones.return_value = []
    add_entities = mock.MagicMock()
    nx584.setup_platform(
        hass,
        DEFAULT_CONFIG,
        add_entities,
    )
    expect(add_entities.called).to_be_falsy()


@test
def nx584_zone_sensor_normal() -> None:
    """Test for the NX584 zone sensor."""
    zone = {"number": 1, "name": "foo", "state": True}
    sensor = nx584.NX584ZoneSensor(zone, "motion")
    expect(sensor.name).to_equal("foo")
    expect(sensor.should_poll).to_be_falsy()
    expect(sensor.is_on).to_be_truthy()
    expect(sensor.extra_state_attributes["zone_number"]).to_equal(1)
    expect(sensor.extra_state_attributes["bypassed"]).to_be_falsy()

    zone["state"] = False
    expect(sensor.is_on).to_be_falsy()


@test
def nx584_zone_sensor_bypassed() -> None:
    """Test for the NX584 zone sensor."""
    zone = {"number": 1, "name": "foo", "state": True, "bypassed": True}
    sensor = nx584.NX584ZoneSensor(zone, "motion")
    expect(sensor.name).to_equal("foo")
    expect(sensor.should_poll).to_be_falsy()
    expect(sensor.is_on).to_be_truthy()
    expect(sensor.extra_state_attributes["zone_number"]).to_equal(1)
    expect(sensor.extra_state_attributes["bypassed"]).to_be_truthy()

    zone["state"] = False
    zone["bypassed"] = False
    expect(sensor.is_on).to_be_falsy()
    expect(sensor.extra_state_attributes["bypassed"]).to_be_falsy()


@test
def nx584_watcher_process_zone_event() -> None:
    """Test the processing of zone events."""
    with mock.patch.object(
        nx584.NX584ZoneSensor, "schedule_update_ha_state"
    ) as mock_update:
        zone1 = {"number": 1, "name": "foo", "state": True}
        zone2 = {"number": 2, "name": "bar", "state": True}
        zones = {
            1: nx584.NX584ZoneSensor(zone1, "motion"),
            2: nx584.NX584ZoneSensor(zone2, "motion"),
        }
        watcher = nx584.NX584Watcher(None, zones)
        watcher._process_zone_event({"zone": 1, "zone_state": False})
        expect(zone1["state"]).to_be_falsy()
        expect(mock_update.call_count).to_equal(1)


@test
def nx584_watcher_process_zone_event_missing_zone() -> None:
    """Test the processing of zone events with missing zones."""
    with mock.patch.object(
        nx584.NX584ZoneSensor, "schedule_update_ha_state"
    ) as mock_update:
        watcher = nx584.NX584Watcher(None, {})
        watcher._process_zone_event({"zone": 1, "zone_state": False})
        expect(mock_update.called).to_be_falsy()


@test
def nx584_watcher_run_with_zone_events() -> None:
    """Test the zone events."""
    empty_me = [1, 2]

    def fake_get_events():
        """Return nothing twice, then some events."""
        if empty_me:
            empty_me.pop()
            return None
        return fake_events

    client = mock.MagicMock()
    fake_events = [
        {"zone": 1, "zone_state": True, "type": "zone_status"},
        {"zone": 2, "foo": False},
    ]
    client.get_events.side_effect = fake_get_events
    watcher = nx584.NX584Watcher(client, {})

    with mock.patch.object(watcher, "_process_zone_event") as fake_process:
        fake_process.side_effect = StopMe
        expect(lambda: watcher._run()).to_raise(StopMe)
        expect(fake_process.call_count).to_equal(1)
        expect(fake_process.call_args).to_equal(mock.call(fake_events[0]))

    expect(client.get_events.call_count).to_equal(3)


@test
def nx584_watcher_run_retries_failures() -> None:
    """Test the retries with failures."""
    empty_me = [1, 2]

    def fake_run():
        """Fake runner."""
        if empty_me:
            empty_me.pop()
            raise requests.exceptions.ConnectionError
        raise StopMe

    with mock.patch("time.sleep") as mock_sleep:
        watcher = nx584.NX584Watcher(None, {})
        with mock.patch.object(watcher, "_run") as mock_inner:
            mock_inner.side_effect = fake_run
            expect(lambda: watcher.run()).to_raise(StopMe)
            expect(mock_inner.call_count).to_equal(3)
        mock_sleep.assert_has_calls([mock.call(10), mock.call(10)])
