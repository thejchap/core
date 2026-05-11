"""Tryke fixtures for the ZHA integration tests.

Ported from ``tests/components/zha/conftest.py``. Mirrors the zigpy
``ControllerApplication`` mock + autouse plumbing originally provided by
the pytest fixtures.
"""

from collections.abc import Callable, Coroutine, Generator
from datetime import timedelta
import itertools
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch
import warnings

from tryke import Depends, fixture
import zhaquirks
import zigpy
from zigpy.application import ControllerApplication
import zigpy.backups
from zigpy.backups import BackupManager
import zigpy.config
from zigpy.const import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
import zigpy.device
import zigpy.group
import zigpy.profiles
from zigpy.profiles import zha
import zigpy.quirks
import zigpy.state
import zigpy.types
import zigpy.util
from zigpy.zcl.clusters.general import Basic, Groups
from zigpy.zcl.foundation import Status
import zigpy.zdo.types as zdo_t

from homeassistant.components.zha import const as zha_const
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import patch_cluster as common_patch_cluster

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

FIXTURE_GRP_ID = 0x1001
FIXTURE_GRP_NAME = "fixture group"
COUNTER_NAMES = ["counter_1", "counter_2", "counter_3"]


@fixture
def globally_load_quirks() -> None:
    """Load quirks automatically so ZHA tests run deterministically."""
    zhaquirks.setup()


@fixture
def disable_platform_only() -> Generator[None]:
    """Disable platforms to speed up tests."""
    with patch("homeassistant.components.zha.PLATFORMS", []):
        yield


@fixture
def mock_multipan_platform() -> Generator[None]:
    """Mock the multipan platform."""
    with (
        patch(
            "homeassistant.components.zha.silabs_multiprotocol.async_get_channel",
            return_value=None,
        ),
        patch(
            "homeassistant.components.zha.silabs_multiprotocol.async_using_multipan",
            return_value=False,
        ),
    ):
        yield


@fixture
def speed_up_radio_mgr() -> Generator[None]:
    """Speed up the radio manager connection time by removing delays."""
    with patch("homeassistant.components.zha.radio_manager.CONNECT_DELAY_S", 0.00001):
        yield


@fixture
def reduce_reconnect_timeout() -> Generator[None]:
    """Reduce reconnect timeout to speed up tests."""
    with patch("homeassistant.components.zha.radio_manager.RETRY_DELAY_S", 0.0001):
        yield


@fixture
def mock_app() -> Generator[AsyncMock]:
    """Mock zigpy app interface.

    Direct port of the ``mock_app`` autouse fixture from the dev branch's
    ``test_config_flow.py``. Patches ``zigpy.application.ControllerApplication.new``
    so config-flow probes resolve through this mock instead of touching real
    radio hardware.
    """
    mock_app = create_autospec(ControllerApplication, instance=True)
    mock_app.backups = create_autospec(BackupManager, instance=True)
    mock_app.backups.backups = []
    mock_app.state = MagicMock()
    mock_app.state.network_info.extended_pan_id = zigpy.types.EUI64.convert(
        "AABBCCDDEE000000"
    )
    mock_app.state.network_info.metadata = {
        "ezsp": {
            "can_burn_userdata_custom_eui64": True,
            "can_rewrite_custom_eui64": False,
        }
    }
    mock_app.add_listener = MagicMock()
    mock_app.groups = MagicMock()
    mock_app.devices = MagicMock()

    with patch(
        "zigpy.application.ControllerApplication.new",
        AsyncMock(return_value=mock_app),
    ):
        yield mock_app


def _make_backup_factory():
    """Create a stateful zigpy NetworkBackup factory."""
    state = {"num_calls": 0}

    def inner(*, backup_time_offset: int = 0) -> zigpy.backups.NetworkBackup:
        backup = zigpy.backups.NetworkBackup()
        backup.backup_time += timedelta(seconds=backup_time_offset)
        backup.node_info.ieee = zigpy.types.EUI64.convert(
            f"AABBCCDDEE{state['num_calls']:06X}"
        )
        state["num_calls"] += 1
        return backup

    return inner


@fixture
def make_backup():
    """Zigpy network backup factory that creates unique backups with each call."""
    return _make_backup_factory()


@fixture
def backup() -> zigpy.backups.NetworkBackup:
    """Zigpy network backup with non-default settings."""
    return _make_backup_factory()()


@fixture
def mock_create_zigpy_app() -> Generator[MagicMock]:
    """Mock the radio connection."""
    mock_connect_app = MagicMock()
    mock_connect_app.__aenter__.return_value.backups.backups = [MagicMock()]
    mock_connect_app.__aenter__.return_value.backups.create_backup.return_value = (
        MagicMock()
    )

    with patch(
        "homeassistant.components.zha.radio_manager.ZhaRadioManager.create_zigpy_app",
        return_value=mock_connect_app,
    ):
        yield mock_connect_app


# ---------------------------------------------------------------------------
# zigpy controller application + setup_zha plumbing
# ---------------------------------------------------------------------------


class _FakeApp(ControllerApplication):
    async def add_endpoint(self, descriptor: zdo_t.SimpleDescriptor):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def force_remove(self, dev: zigpy.device.Device):
        pass

    async def load_network_info(self, *, load_devices: bool = False):
        pass

    async def permit_ncp(self, time_s: int = 60):
        pass

    async def permit_with_link_key(
        self, node: zigpy.types.EUI64, link_key: zigpy.types.KeyData, time_s: int = 60
    ):
        pass

    async def reset_network_info(self):
        pass

    async def send_packet(self, packet: zigpy.types.ZigbeePacket):
        pass

    async def start_network(self):
        pass

    async def write_network_info(
        self, *, network_info: zigpy.state.NetworkInfo, node_info: zigpy.state.NodeInfo
    ) -> None:
        pass

    async def request(
        self,
        device: zigpy.device.Device,
        profile: zigpy.types.uint16_t,
        cluster: zigpy.types.uint16_t,
        src_ep: zigpy.types.uint8_t,
        dst_ep: zigpy.types.uint8_t,
        sequence: zigpy.types.uint8_t,
        data: bytes,
        *,
        expect_reply: bool = True,
        use_ieee: bool = False,
        extended_timeout: bool = False,
    ):
        pass

    async def move_network_to_channel(
        self, new_channel: int, *, num_broadcasts: int = 5
    ) -> None:
        pass

    def _persist_coordinator_model_strings_in_db(self) -> None:
        pass


def _wrap_mock_instance(obj: Any) -> MagicMock:
    """Auto-mock every attribute and method in an object."""
    mock = create_autospec(obj, spec_set=True, instance=True)

    for attr_name in dir(obj):
        if attr_name.startswith("__") and attr_name != "__getitem__":
            continue

        real_attr = getattr(obj, attr_name)
        mock_attr = getattr(mock, attr_name)

        if callable(real_attr) and not hasattr(real_attr, "__aenter__"):
            mock_attr.side_effect = real_attr
        else:
            setattr(mock, attr_name, real_attr)

    return mock


@fixture
async def zigpy_app_controller() -> Generator[ControllerApplication]:
    """Zigpy ApplicationController fixture."""
    app = _FakeApp(
        {
            zigpy.config.CONF_DATABASE: None,
            zigpy.config.CONF_DEVICE: {zigpy.config.CONF_DEVICE_PATH: "/dev/null"},
            zigpy.config.CONF_STARTUP_ENERGY_SCAN: False,
            zigpy.config.CONF_NWK_BACKUP_ENABLED: False,
            zigpy.config.CONF_TOPO_SCAN_ENABLED: False,
            zigpy.config.CONF_OTA: {
                zigpy.config.CONF_OTA_ENABLED: False,
            },
        }
    )

    app.groups.add_group(FIXTURE_GRP_ID, FIXTURE_GRP_NAME, suppress_event=True)

    app.state.node_info.nwk = 0x0000
    app.state.node_info.ieee = zigpy.types.EUI64.convert("00:15:8d:00:02:32:4f:32")
    app.state.node_info.manufacturer = "Coordinator Manufacturer"
    app.state.node_info.model = "Coordinator Model"
    app.state.node_info.version = "7.1.4.0 build 389"
    app.state.network_info.pan_id = 0x1234
    app.state.network_info.extended_pan_id = app.state.node_info.ieee
    app.state.network_info.channel = 15
    app.state.network_info.network_key.key = zigpy.types.KeyData(range(16))
    app.state.counters = zigpy.state.CounterGroups()
    app.state.counters["ezsp_counters"] = zigpy.state.CounterGroup("ezsp_counters")
    for name in COUNTER_NAMES:
        app.state.counters["ezsp_counters"][name].increment()

    # Create a fake coordinator device
    dev = app.add_device(nwk=app.state.node_info.nwk, ieee=app.state.node_info.ieee)
    dev.node_desc = zdo_t.NodeDescriptor()
    dev.node_desc.logical_type = zdo_t.LogicalType.Coordinator
    dev.manufacturer = "Coordinator Manufacturer"
    dev.model = "Coordinator Model"

    ep = dev.add_endpoint(1)
    ep.profile_id = zha.PROFILE_ID
    ep.add_input_cluster(Basic.cluster_id)
    ep.add_input_cluster(Groups.cluster_id)

    with patch("zigpy.device.Device.request", return_value=[Status.SUCCESS]):
        # The mock wrapping accesses deprecated attributes, so we suppress the warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mock_app = _wrap_mock_instance(app)
            mock_app.backups = _wrap_mock_instance(app.backups)
            mock_app._concurrent_requests_semaphore = _wrap_mock_instance(
                app._concurrent_requests_semaphore
            )

        yield mock_app


@fixture
async def config_entry() -> MockConfigEntry:
    """Fixture representing a config entry."""
    return MockConfigEntry(
        version=5,
        domain=zha_const.DOMAIN,
        data={
            zigpy.config.CONF_DEVICE: {
                zigpy.config.CONF_DEVICE_PATH: "/dev/ttyUSB0",
                zigpy.config.CONF_DEVICE_BAUDRATE: 115200,
                zigpy.config.CONF_DEVICE_FLOW_CONTROL: "hardware",
            },
            zha_const.CONF_RADIO_TYPE: "ezsp",
        },
        options={
            zha_const.CUSTOM_CONFIGURATION: {
                zha_const.ZHA_OPTIONS: {
                    zha_const.CONF_ENABLE_ENHANCED_LIGHT_TRANSITION: True,
                    zha_const.CONF_GROUP_MEMBERS_ASSUME_STATE: False,
                },
                zha_const.ZHA_ALARM_OPTIONS: {
                    zha_const.CONF_ALARM_ARM_REQUIRES_CODE: False,
                    zha_const.CONF_ALARM_MASTER_CODE: "4321",
                    zha_const.CONF_ALARM_FAILED_TRIES: 2,
                },
            }
        },
    )


@fixture
def mock_zigpy_connect(
    zigpy_app_controller: ControllerApplication = Depends(zigpy_app_controller),
) -> Generator[ControllerApplication]:
    """Patch the zigpy radio connection with our mock application."""
    with (
        patch(
            "bellows.zigbee.application.ControllerApplication.new",
            return_value=zigpy_app_controller,
        ),
        patch(
            "bellows.zigbee.application.ControllerApplication",
            return_value=zigpy_app_controller,
        ),
    ):
        yield zigpy_app_controller


@fixture
def setup_zha(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
    mock_zigpy_connect: ControllerApplication = Depends(mock_zigpy_connect),
) -> Callable[..., Coroutine[None]]:
    """Set up ZHA component."""
    zha_config = {zha_const.CONF_ENABLE_QUIRKS: False}

    async def _setup(config=None) -> None:
        config_entry.add_to_hass(hass)
        config = config or {}

        status = await async_setup_component(
            hass, zha_const.DOMAIN, {zha_const.DOMAIN: {**zha_config, **config}}
        )
        assert status is True
        await hass.async_block_till_done()

    return _setup


@fixture
def cluster_handler() -> Callable[..., MagicMock]:
    """ClusterHandler mock factory fixture."""

    def _cluster_handler(name: str, cluster_id: int, endpoint_id: int = 1):
        ch = MagicMock()
        ch.name = name
        ch.generic_id = f"cluster_handler_0x{cluster_id:04x}"
        ch.id = f"{endpoint_id}:0x{cluster_id:04x}"
        ch.async_configure = AsyncMock()
        ch.async_initialize = AsyncMock()
        return ch

    return _cluster_handler


@fixture
def network_backup() -> zigpy.backups.NetworkBackup:
    """Real ZHA network backup taken from an active instance."""
    return zigpy.backups.NetworkBackup.from_dict(
        {
            "backup_time": "2022-11-16T03:16:49.427675+00:00",
            "network_info": {
                "extended_pan_id": "2f:73:58:bd:fe:78:91:11",
                "pan_id": "2DB4",
                "nwk_update_id": 0,
                "nwk_manager_id": "0000",
                "channel": 15,
                "channel_mask": [
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                ],
                "security_level": 5,
                "network_key": {
                    "key": "4a:c7:9d:50:51:09:16:37:2e:34:66:c6:ed:9b:23:85",
                    "tx_counter": 14131,
                    "rx_counter": 0,
                    "seq": 0,
                    "partner_ieee": "ff:ff:ff:ff:ff:ff:ff:ff",
                },
                "tc_link_key": {
                    "key": "5a:69:67:42:65:65:41:6c:6c:69:61:6e:63:65:30:39",
                    "tx_counter": 0,
                    "rx_counter": 0,
                    "seq": 0,
                    "partner_ieee": "84:ba:20:ff:fe:59:f5:ff",
                },
                "key_table": [],
                "children": [],
                "nwk_addresses": {"cc:cc:cc:ff:fe:e6:8e:ca": "1431"},
                "stack_specific": {
                    "ezsp": {"hashed_tclk": "e9bd3ac165233d95923613c608beb147"}
                },
                "metadata": {
                    "ezsp": {
                        "manufacturer": "",
                        "board": "",
                        "version": "7.1.3.0 build 0",
                        "stack_version": 9,
                        "can_write_custom_eui64": False,
                    }
                },
                "source": "bellows@0.34.2",
            },
            "node_info": {
                "nwk": "0000",
                "ieee": "84:ba:20:ff:fe:59:f5:ff",
                "logical_type": "coordinator",
            },
        }
    )


@fixture
def zigpy_device_mock(
    zigpy_app_controller: ControllerApplication = Depends(zigpy_app_controller),
) -> Callable[..., zigpy.device.Device]:
    """Make a fake device using the specified cluster classes."""

    def _mock_dev(
        endpoints,
        ieee="00:0d:6f:00:0a:90:69:e7",
        manufacturer="FakeManufacturer",
        model="FakeModel",
        node_descriptor=b"\x02@\x807\x10\x7fd\x00\x00*d\x00\x00",
        nwk=0xB79C,
        patch_cluster=True,
        quirk=None,
        attributes=None,
    ):
        """Make a fake device using the specified cluster classes."""
        device = zigpy.device.Device(
            zigpy_app_controller, zigpy.types.EUI64.convert(ieee), nwk
        )
        device.manufacturer = manufacturer
        device.model = model
        device.node_desc = zdo_t.NodeDescriptor.deserialize(node_descriptor)[0]
        device.last_seen = time.time()

        for epid, ep in endpoints.items():
            endpoint = device.add_endpoint(epid)
            endpoint.device_type = ep[SIG_EP_TYPE]
            endpoint.profile_id = ep.get(SIG_EP_PROFILE, 0x0104)
            endpoint.request = AsyncMock()

            for cluster_id in ep.get(SIG_EP_INPUT, []):
                endpoint.add_input_cluster(cluster_id)

            for cluster_id in ep.get(SIG_EP_OUTPUT, []):
                endpoint.add_output_cluster(cluster_id)

        device.status = zigpy.device.Status.ENDPOINTS_INIT

        if quirk:
            device = quirk(zigpy_app_controller, device.ieee, device.nwk, device)
        else:
            # Allow zigpy to apply quirks if we don't pass one explicitly
            device = zigpy.quirks.get_device(device)

        if patch_cluster:
            for endpoint in (ep for epid, ep in device.endpoints.items() if epid):
                endpoint.request = AsyncMock(return_value=[0])
                for cluster in itertools.chain(
                    endpoint.in_clusters.values(), endpoint.out_clusters.values()
                ):
                    common_patch_cluster(cluster)

        if attributes is not None:
            for ep_id, clusters in attributes.items():
                for cluster_name, attrs in clusters.items():
                    cluster = getattr(device.endpoints[ep_id], cluster_name)

                    for name, value in attrs.items():
                        attr_id = cluster.find_attribute(name).id
                        cluster._attr_cache[attr_id] = value

        return device

    return _mock_dev
