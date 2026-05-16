"""The tests for the device tracker component."""

from datetime import datetime, timedelta
import json
import logging
from unittest.mock import call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import device_tracker, zone
from homeassistant.components.device_tracker import SourceType, const, legacy
from homeassistant.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_GPS_ACCURACY,
    ATTR_ICON,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_PLATFORM,
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import discovery
from homeassistant.helpers.json import JSONEncoder
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import common
from ._fixtures import (
    hass as hass_fixture,
    mock_device_tracker_conf as mock_device_tracker_conf_fx,
    mock_legacy_device_scanner as mock_legacy_device_scanner_fx,
    mock_legacy_setup as mock_legacy_setup_fx,
    yaml_devices as yaml_devices_fx,
)
from .common import MockScanner

from tests.common import (
    RegistryEntryWithDefaults,
    assert_setup_component,
    async_fire_time_changed,
    mock_registry,
    mock_restore_cache,
    patch_yaml_files,
)
from tests.hass_fixtures import caplog as caplog_fx, mock_network
from tests.hass_tryke_helpers import expect_raises_async

TEST_PLATFORM = {device_tracker.DOMAIN: {CONF_PLATFORM: "test"}}

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor fixture."""
    return 0


@test
async def is_on(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test is_on method."""
    entity_id = f"{const.DOMAIN}.test"

    hass.states.async_set(entity_id, STATE_HOME)

    expect(device_tracker.is_on(hass, entity_id)).to_be_truthy()

    hass.states.async_set(entity_id, STATE_NOT_HOME)

    expect(device_tracker.is_on(hass, entity_id)).to_be_falsy()


@test
async def reading_broken_yaml_config(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test when known devices contains invalid data."""
    files = {
        "empty.yaml": "",
        "nodict.yaml": "100",
        "badkey.yaml": "@:\n  name: Device",
        "noname.yaml": "my_device:\n",
        "allok.yaml": "My Device:\n  name: Device",
        "oneok.yaml": "My Device!:\n  name: Device\nbad_device:\n  nme: Device",
    }
    args = {"hass": hass, "consider_home": timedelta(seconds=60)}
    with patch_yaml_files(files):
        expect(await legacy.async_load_config("empty.yaml", **args)).to_equal([])
        expect(await legacy.async_load_config("nodict.yaml", **args)).to_equal([])
        expect(await legacy.async_load_config("noname.yaml", **args)).to_equal([])
        expect(await legacy.async_load_config("badkey.yaml", **args)).to_equal([])

        res = await legacy.async_load_config("allok.yaml", **args)
        expect(len(res)).to_equal(1)
        expect(res[0].name).to_equal("Device")
        expect(res[0].dev_id).to_equal("my_device")

        res = await legacy.async_load_config("oneok.yaml", **args)
        expect(len(res)).to_equal(1)
        expect(res[0].name).to_equal("Device")
        expect(res[0].dev_id).to_equal("my_device")


@test
async def reading_yaml_config(
    hass: HomeAssistant = Depends(hass_fixture),
    yaml_devices: str = Depends(yaml_devices_fx),
) -> None:
    """Test the rendering of the YAML configuration."""
    dev_id = "test"
    device = legacy.Device(
        hass,
        timedelta(seconds=180),
        True,
        dev_id,
        "AB:CD:EF:GH:IJ",
        "Test name",
        picture="http://test.picture",
        icon="mdi:kettle",
    )
    await hass.async_add_executor_job(
        legacy.update_config, yaml_devices, dev_id, device
    )
    loaded_config = None
    original_async_load_config = legacy.async_load_config

    async def capture_load_config(*args, **kwargs):
        nonlocal loaded_config
        loaded_config = await original_async_load_config(*args, **kwargs)
        return loaded_config

    with patch(
        "homeassistant.components.device_tracker.legacy.async_load_config",
        capture_load_config,
    ):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()
    config = loaded_config[0]
    expect(device.dev_id).to_equal(config.dev_id)
    expect(device.track).to_equal(config.track)
    expect(device.mac).to_equal(config.mac)
    expect(device.config_picture).to_equal(config.config_picture)
    expect(device.consider_home).to_equal(config.consider_home)
    expect(device.icon).to_equal(config.icon)
    expect(f"test.{device_tracker.DOMAIN}" in hass.config.components).to_be_truthy()


@test
async def duplicate_mac_dev_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test adding duplicate MACs or device IDs to DeviceTracker."""
    with patch(
        "homeassistant.components.device_tracker.const.LOGGER.warning"
    ) as mock_warning:
        devices = [
            legacy.Device(
                hass, True, True, "my_device", "AB:01", "My device", None, None, False
            ),
            legacy.Device(
                hass,
                True,
                True,
                "your_device",
                "AB:01",
                "Your device",
                None,
                None,
                False,
            ),
        ]
        legacy.DeviceTracker(hass, False, True, {}, devices)
        _LOGGER.debug(mock_warning.call_args_list)
        expect(mock_warning.call_count).to_equal(1)
        args, _ = mock_warning.call_args
        expect("Duplicate device MAC" in args[0]).to_be_truthy()

        mock_warning.reset_mock()
        devices = [
            legacy.Device(
                hass, True, True, "my_device", "AB:01", "My device", None, None, False
            ),
            legacy.Device(
                hass, True, True, "my_device", None, "Your device", None, None, False
            ),
        ]
        legacy.DeviceTracker(hass, False, True, {}, devices)

        _LOGGER.debug(mock_warning.call_args_list)
        expect(mock_warning.call_count).to_equal(1)
        args, _ = mock_warning.call_args
        expect("Duplicate device IDs" in args[0]).to_be_truthy()


@test
async def setup_without_yaml_file(
    hass: HomeAssistant = Depends(hass_fixture),
    yaml_devices: str = Depends(yaml_devices_fx),
) -> None:
    """Test with no YAML file."""
    with assert_setup_component(1, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()


@test
async def gravatar(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test the Gravatar generation."""
    dev_id = "test"
    device = legacy.Device(
        hass,
        timedelta(seconds=180),
        True,
        dev_id,
        "AB:CD:EF:GH:IJ",
        "Test name",
        gravatar="test@example.com",
    )
    gravatar_url = (
        "https://www.gravatar.com/avatar/"
        "55502f40dc8b7c769880b10874abc9d0.jpg?s=80&d=wavatar"
    )
    expect(device.config_picture).to_equal(gravatar_url)


@test
async def gravatar_and_picture(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that Gravatar overrides picture."""
    dev_id = "test"
    device = legacy.Device(
        hass,
        timedelta(seconds=180),
        True,
        dev_id,
        "AB:CD:EF:GH:IJ",
        "Test name",
        picture="http://test.picture",
        gravatar="test@example.com",
    )
    gravatar_url = (
        "https://www.gravatar.com/avatar/"
        "55502f40dc8b7c769880b10874abc9d0.jpg?s=80&d=wavatar"
    )
    expect(device.config_picture).to_equal(gravatar_url)


@test
async def discover_platform(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test discovery of device_tracker demo platform."""
    with (
        patch(
            "homeassistant.components.device_tracker.legacy.DeviceTracker.see"
        ) as mock_see,
        patch(
            "homeassistant.components.demo.device_tracker.setup_scanner",
            autospec=True,
        ) as mock_demo_setup_scanner,
    ):
        await async_setup_component(hass, "homeassistant", {})
        await async_setup_component(hass, device_tracker.DOMAIN, {})
        # async_block_till_done is intentionally missing here so we
        # can verify async_load_platform still works without it
        with patch("homeassistant.components.device_tracker.legacy.update_config"):
            await discovery.async_load_platform(
                hass,
                device_tracker.DOMAIN,
                "demo",
                {"test_key": "test_val"},
                {"bla": {}},
            )
            await hass.async_block_till_done()
        expect(device_tracker.DOMAIN in hass.config.components).to_be_truthy()
        expect(mock_demo_setup_scanner.called).to_be_truthy()
        expect(mock_demo_setup_scanner.call_args[0]).to_equal(
            (hass, {}, mock_see, {"test_key": "test_val"})
        )


@test
async def discover_platform_missing_platform(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog=Depends(caplog_fx),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test discovery of device_tracker missing platform."""
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, device_tracker.DOMAIN, {})
    # async_block_till_done is intentionally missing here so we
    # can verify async_load_platform still works without it
    with patch("homeassistant.components.device_tracker.legacy.update_config"):
        await discovery.async_load_platform(
            hass,
            device_tracker.DOMAIN,
            "its_not_there",
            {"test_key": "test_val"},
            {"bla": {}},
        )
        await hass.async_block_till_done()
    expect(device_tracker.DOMAIN in hass.config.components).to_be_truthy()
    expect(
        "Unable to prepare setup for platform 'its_not_there.device_tracker'"
        in caplog.text
    ).to_be_truthy()


@test
async def update_stale(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    mock_legacy_device_scanner: MockScanner = Depends(mock_legacy_device_scanner_fx),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test stalled update."""
    mock_legacy_device_scanner.reset()
    mock_legacy_device_scanner.come_home("DEV1")

    now = dt_util.utcnow()
    register_time = datetime(now.year + 1, 9, 15, 23, tzinfo=dt_util.UTC)
    scan_time = datetime(now.year + 1, 9, 15, 23, 1, tzinfo=dt_util.UTC)

    with (
        patch(
            "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
            return_value=register_time,
        ),
        assert_setup_component(1, device_tracker.DOMAIN),
    ):
        expect(
            await async_setup_component(
                hass,
                device_tracker.DOMAIN,
                {
                    device_tracker.DOMAIN: {
                        CONF_PLATFORM: "test",
                        device_tracker.CONF_CONSIDER_HOME: 59,
                    }
                },
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

    expect(hass.states.get("device_tracker.dev1").state).to_equal(STATE_HOME)

    mock_legacy_device_scanner.leave_home("DEV1")

    with patch(
        "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
        return_value=scan_time,
    ):
        async_fire_time_changed(hass, scan_time)
        await hass.async_block_till_done()

    expect(hass.states.get("device_tracker.dev1").state).to_equal(STATE_NOT_HOME)


@test
async def entity_attributes(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test the entity attributes."""
    devices = mock_device_tracker_conf
    dev_id = "test_entity"
    entity_id = f"{const.DOMAIN}.{dev_id}"
    friendly_name = "Paulus"
    picture = "http://placehold.it/200x200"
    icon = "mdi:kettle"

    device = legacy.Device(
        hass,
        timedelta(seconds=180),
        True,
        dev_id,
        None,
        friendly_name,
        picture,
        icon=icon,
    )
    devices.append(device)

    with assert_setup_component(1, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()

    attrs = hass.states.get(entity_id).attributes

    expect(attrs.get(ATTR_FRIENDLY_NAME)).to_equal(friendly_name)
    expect(attrs.get(ATTR_ICON)).to_equal(icon)
    expect(attrs.get(ATTR_ENTITY_PICTURE)).to_equal(picture)


@test
async def see_service(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test the see service with a unicode dev_id and NO MAC."""
    with patch(
        "homeassistant.components.device_tracker.legacy.DeviceTracker.async_see"
    ) as mock_see:
        with assert_setup_component(1, device_tracker.DOMAIN):
            expect(
                await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
            ).to_be_truthy()
            await hass.async_block_till_done()
        params = {
            "dev_id": "some_device",
            "host_name": "example.com",
            "location_name": "Work",
            "gps": [0.3, 0.8],
            "attributes": {"test": "test"},
        }
        common.async_see(hass, **params)
        await hass.async_block_till_done()
        expect(mock_see.call_count).to_equal(1)
        expect(mock_see.call_args).to_equal(call(**params))

        mock_see.reset_mock()
        params["dev_id"] += chr(233)  # e' acute accent from icloud

        common.async_see(hass, **params)
        await hass.async_block_till_done()
        expect(mock_see.call_count).to_equal(1)
        expect(mock_see.call_args).to_equal(call(**params))


@test
async def see_service_guard_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test the guard if the device is registered in the entity registry."""
    dev_id = "test"
    entity_id = f"{const.DOMAIN}.{dev_id}"
    mock_registry(
        hass,
        {
            entity_id: RegistryEntryWithDefaults(
                entity_id=entity_id, unique_id=1, platform=const.DOMAIN
            )
        },
    )
    devices = mock_device_tracker_conf
    expect(
        await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
    ).to_be_truthy()
    await hass.async_block_till_done()
    params = {"dev_id": dev_id, "gps": [0.3, 0.8]}

    common.async_see(hass, **params)
    await hass.async_block_till_done()

    expect(devices).to_be_falsy()


@test
async def new_device_event_fired(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that the device tracker will fire an event."""
    with assert_setup_component(1, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()
    test_events = []

    @callback
    def listener(event):
        """Record that our event got called."""
        test_events.append(event)

    hass.bus.async_listen("device_tracker_new_device", listener)

    common.async_see(hass, "mac_1", host_name="hello")
    common.async_see(hass, "mac_1", host_name="hello")

    await hass.async_block_till_done()

    expect(len(test_events)).to_equal(1)

    # Assert we can serialize the event
    json.dumps(test_events[0].as_dict(), cls=JSONEncoder)

    expect(test_events[0].data).to_equal(
        {
            "entity_id": "device_tracker.hello",
            "host_name": "hello",
            "mac": "MAC_1",
        }
    )


@test
async def duplicate_yaml_keys(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that the device tracker will not generate invalid YAML."""
    devices = mock_device_tracker_conf
    with assert_setup_component(1, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()

    common.async_see(hass, "mac_1", host_name="hello")
    common.async_see(hass, "mac_2", host_name="hello")

    await hass.async_block_till_done()

    expect(len(devices)).to_equal(2)
    expect(devices[0].dev_id != devices[1].dev_id).to_be_truthy()


@test
async def invalid_dev_id(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that the device tracker will not allow invalid dev ids."""
    devices = mock_device_tracker_conf
    with assert_setup_component(1, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        ).to_be_truthy()
        await hass.async_block_till_done()

    common.async_see(hass, dev_id="hello-world")
    await hass.async_block_till_done()

    expect(devices).to_be_falsy()


@test
async def see_state(
    hass: HomeAssistant = Depends(hass_fixture),
    yaml_devices: str = Depends(yaml_devices_fx),
) -> None:
    """Test device tracker see records state correctly."""
    expect(
        await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
    ).to_be_truthy()
    await hass.async_block_till_done()

    params = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "dev_id": "some_device",
        "host_name": "example.com",
        "location_name": "Work",
        "gps": [0.3, 0.8],
        "gps_accuracy": 1,
        "battery": 100,
        "attributes": {"test": "test", "number": 1},
    }

    common.async_see(hass, **params)
    await hass.async_block_till_done()

    config = await legacy.async_load_config(yaml_devices, hass, timedelta(seconds=0))
    expect(len(config)).to_equal(1)

    state = hass.states.get("device_tracker.example_com")
    attrs = state.attributes
    expect(state.state).to_equal("Work")
    expect(state.object_id).to_equal("example_com")
    expect(state.name).to_equal("example.com")
    expect(attrs["friendly_name"]).to_equal("example.com")
    expect(attrs["battery"]).to_equal(100)
    expect(attrs["latitude"]).to_equal(0.3)
    expect(attrs["longitude"]).to_equal(0.8)
    expect(attrs["test"]).to_equal("test")
    expect(attrs["gps_accuracy"]).to_equal(1)
    expect(attrs["source_type"]).to_equal("gps")
    expect(attrs["number"]).to_equal(1)


@test
async def see_passive_zone_state(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    mock_legacy_device_scanner: MockScanner = Depends(mock_legacy_device_scanner_fx),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that the device tracker sets gps for passive trackers."""
    now = dt_util.utcnow()

    register_time = datetime(now.year + 1, 9, 15, 23, tzinfo=dt_util.UTC)
    scan_time = datetime(now.year + 1, 9, 15, 23, 1, tzinfo=dt_util.UTC)

    with assert_setup_component(1, zone.DOMAIN):
        zone_info = {
            "name": "Home",
            "latitude": 1,
            "longitude": 2,
            "radius": 250,
            "passive": False,
        }

        await async_setup_component(hass, zone.DOMAIN, {"zone": zone_info})
        await hass.async_block_till_done()

    mock_legacy_device_scanner.reset()
    mock_legacy_device_scanner.come_home("dev1")

    with (
        patch(
            "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
            return_value=register_time,
        ),
        assert_setup_component(1, device_tracker.DOMAIN),
    ):
        expect(
            await async_setup_component(
                hass,
                device_tracker.DOMAIN,
                {
                    device_tracker.DOMAIN: {
                        CONF_PLATFORM: "test",
                        device_tracker.CONF_CONSIDER_HOME: 59,
                    }
                },
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

    state = hass.states.get("device_tracker.dev1")
    attrs = state.attributes
    expect(state.state).to_equal(STATE_HOME)
    expect(state.object_id).to_equal("dev1")
    expect(state.name).to_equal("dev1")
    expect(attrs.get("friendly_name")).to_equal("dev1")
    expect(attrs.get("latitude")).to_equal(1)
    expect(attrs.get("longitude")).to_equal(2)
    expect(attrs.get("gps_accuracy")).to_equal(0)
    expect(attrs.get("source_type")).to_equal(SourceType.ROUTER)

    mock_legacy_device_scanner.leave_home("dev1")

    with patch(
        "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
        return_value=scan_time,
    ):
        async_fire_time_changed(hass, scan_time)
        await hass.async_block_till_done()

    state = hass.states.get("device_tracker.dev1")
    attrs = state.attributes
    expect(state.state).to_equal(STATE_NOT_HOME)
    expect(state.object_id).to_equal("dev1")
    expect(state.name).to_equal("dev1")
    expect(attrs.get("friendly_name")).to_equal("dev1")
    expect(attrs.get("latitude")).to_be_none()
    expect(attrs.get("longitude")).to_be_none()
    expect(attrs.get("gps_accuracy")).to_be_none()
    expect(attrs.get("source_type")).to_equal(SourceType.ROUTER)


@test
async def see_failures(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that the device tracker see failures."""
    with patch(
        "homeassistant.components.device_tracker.const.LOGGER.warning"
    ) as mock_warning:
        devices = mock_device_tracker_conf
        tracker = legacy.DeviceTracker(hass, timedelta(seconds=60), 0, {}, [])

        # MAC is not a string (but added)
        await tracker.async_see(mac=567, host_name="Number MAC")

        # No device id or MAC(not added)
        async with expect_raises_async(HomeAssistantError):
            await tracker.async_see()
        expect(mock_warning.call_count).to_equal(0)

        # Ignore gps on invalid GPS (both added & warnings)
        await tracker.async_see(mac="mac_1_bad_gps", gps=1)
        await tracker.async_see(mac="mac_2_bad_gps", gps=[1])
        await tracker.async_see(mac="mac_3_bad_gps", gps="gps")
        await hass.async_block_till_done()

        expect(mock_warning.call_count).to_equal(3)
        expect(len(devices)).to_equal(4)


@test
async def async_added_to_hass(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test restoring state."""
    attr = {
        ATTR_LONGITUDE: 18,
        ATTR_LATITUDE: -33,
        const.ATTR_SOURCE_TYPE: "gps",
        ATTR_GPS_ACCURACY: 2,
        const.ATTR_BATTERY: 100,
    }
    mock_restore_cache(hass, [State("device_tracker.jk", "home", attr)])

    path = hass.config.path(legacy.YAML_DEVICES)

    files = {path: "jk:\n  name: JK Phone\n  track: True"}
    with patch_yaml_files(files):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, {})
        ).to_be_truthy()
        await hass.async_block_till_done()

    state = hass.states.get("device_tracker.jk")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("home")

    for key, val in attr.items():
        atr = state.attributes.get(key)
        expect(atr).to_equal(val)


@test
async def bad_platform(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test bad platform."""
    config = {"device_tracker": [{"platform": "bad_platform"}]}
    with assert_setup_component(0, device_tracker.DOMAIN):
        expect(
            await async_setup_component(hass, device_tracker.DOMAIN, config)
        ).to_be_truthy()
        await hass.async_block_till_done()

    expect(
        f"bad_platform.{device_tracker.DOMAIN}" not in hass.config.components
    ).to_be_truthy()


@test
async def adding_unknown_device_to_config(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    mock_legacy_device_scanner: MockScanner = Depends(mock_legacy_device_scanner_fx),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test the adding of unknown devices to configuration file."""
    mock_legacy_device_scanner.reset()
    mock_legacy_device_scanner.come_home("DEV1")

    await async_setup_component(
        hass, device_tracker.DOMAIN, {device_tracker.DOMAIN: {CONF_PLATFORM: "test"}}
    )

    await hass.async_block_till_done()

    expect(len(mock_device_tracker_conf)).to_equal(1)
    device = mock_device_tracker_conf[0]
    expect(device.dev_id).to_equal("dev1")
    expect(device.track).to_be_truthy()


@test
async def picture_and_icon_on_see_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test that picture and icon are set in initial see."""
    tracker = legacy.DeviceTracker(hass, timedelta(seconds=60), False, {}, [])
    await tracker.async_see(dev_id=11, picture="pic_url", icon="mdi:icon")
    await hass.async_block_till_done()
    expect(len(mock_device_tracker_conf)).to_equal(1)
    expect(mock_device_tracker_conf[0].icon).to_equal("mdi:icon")
    expect(mock_device_tracker_conf[0].entity_picture).to_equal("pic_url")


@test
async def backward_compatibility_for_track_new(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test backward compatibility for track new."""
    tracker = legacy.DeviceTracker(
        hass, timedelta(seconds=60), False, {device_tracker.CONF_TRACK_NEW: True}, []
    )
    await tracker.async_see(dev_id=13)
    await hass.async_block_till_done()
    expect(len(mock_device_tracker_conf)).to_equal(1)
    expect(mock_device_tracker_conf[0].track).to_be_falsy()


@test
async def old_style_track_new_is_skipped(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device_tracker_conf: list[legacy.Device] = Depends(
        mock_device_tracker_conf_fx
    ),
    _setup: None = Depends(mock_legacy_setup_fx),
) -> None:
    """Test old style config is skipped."""
    tracker = legacy.DeviceTracker(
        hass, timedelta(seconds=60), None, {device_tracker.CONF_TRACK_NEW: False}, []
    )
    await tracker.async_see(dev_id=14)
    await hass.async_block_till_done()
    expect(len(mock_device_tracker_conf)).to_equal(1)
    expect(mock_device_tracker_conf[0].track).to_be_falsy()


@test
def see_schema_allowing_ios_calls() -> None:
    """Test SEE service schema allows extra keys.

    Temp work around because the iOS app sends incorrect data.
    """
    device_tracker.SERVICE_SEE_PAYLOAD_SCHEMA(
        {
            "dev_id": "Test",
            "battery": 35,
            "battery_status": "Not Charging",
            "gps": [10.0, 10.0],
            "gps_accuracy": 300,
            "hostname": "beer",
        }
    )
