"""Tryke fixtures for apple_tv config flow tests.

Mirrors the autouse pyatv scan/pair patches and zero-aggregation-time
patch from upstream ``conftest.py``. Per-device scan-result fixtures
(``mrp_device``, ``dmap_device``, ``full_device`` ...) seed
``mock_scan.result`` with a ``conf.AppleTV`` so the config flow finds
something to pair with.
"""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from pyatv import conf
from pyatv.const import PairingRequirement, Protocol
from pyatv.support import http
from tryke import Depends, fixture

from homeassistant.components.apple_tv import config_flow as apple_tv_config_flow

from .common import MockPairingHandler, airplay_service, create_conf, mrp_service

from tests.hass_tryke_helpers import mock_async_zeroconf as _mock_async_zeroconf


@fixture
def zero_aggregation_time() -> Generator[None]:
    """Prevent discovery aggregation from delaying tests."""
    with patch.object(apple_tv_config_flow, "DISCOVERY_AGGREGATION_TIME", 0):
        yield


@fixture
def use_mocked_zeroconf(
    _mock_zc: MagicMock = Depends(_mock_async_zeroconf),
) -> None:
    """Mock zeroconf in all tests (alias for module-local _trigger_executor)."""


@fixture
def mock_setup_entry() -> Generator[Mock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.apple_tv.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@fixture
def mock_scan() -> Generator[AsyncMock]:
    """Mock pyatv.scan."""
    with patch(
        "homeassistant.components.apple_tv.config_flow.scan"
    ) as scan_mock:

        async def _scan(
            loop, timeout=5, identifier=None, protocol=None, hosts=None, aiozc=None
        ):
            if not scan_mock.hosts:
                scan_mock.hosts = hosts
            return scan_mock.result

        scan_mock.result = []
        scan_mock.hosts = None
        scan_mock.side_effect = _scan
        yield scan_mock


@fixture
def dmap_pin() -> Generator[MagicMock]:
    """Mock random pin generation to a deterministic value."""
    with patch(
        "homeassistant.components.apple_tv.config_flow.randrange"
    ) as mock_pin:
        mock_pin.side_effect = lambda start, stop: 1111
        yield mock_pin


@fixture
def pairing() -> Generator[AsyncMock]:
    """Mock pyatv.pair returning a real-ish MockPairingHandler."""
    with patch(
        "homeassistant.components.apple_tv.config_flow.pair"
    ) as mock_pair:

        async def _pair(config, protocol, loop, session=None, **kwargs):
            handler = MockPairingHandler(
                await http.create_session(session), config.get_service(protocol)
            )
            handler.always_fail = mock_pair.always_fail
            return handler

        mock_pair.always_fail = False
        mock_pair.side_effect = _pair
        yield mock_pair


@fixture
def pairing_mock() -> Generator[AsyncMock]:
    """Mock pyatv.pair returning the mock itself (for behavioural tests)."""
    with patch(
        "homeassistant.components.apple_tv.config_flow.pair"
    ) as mock_pair:

        async def _pair(config, protocol, loop, session=None, **kwargs):
            return mock_pair

        async def _begin():
            pass

        async def _close():
            pass

        mock_pair.close.side_effect = _close
        mock_pair.begin.side_effect = _begin
        mock_pair.pin = lambda pin: None
        mock_pair.side_effect = _pair
        yield mock_pair


@fixture
def mrp_device(scan: AsyncMock = Depends(mock_scan)) -> AsyncMock:
    """Seed scan with two MRP devices (primary + unrelated)."""
    scan.result.extend(
        [
            create_conf(
                "127.0.0.1",
                "MRP Device",
                mrp_service(),
            ),
            create_conf(
                "127.0.0.2",
                "MRP Device 2",
                mrp_service(unique_id="unrelated"),
            ),
        ]
    )
    return scan


@fixture
def full_device(
    scan: AsyncMock = Depends(mock_scan),
    _pin: MagicMock = Depends(dmap_pin),
) -> AsyncMock:
    """Seed scan with a device offering MRP+DMAP+AirPlay."""
    scan.result.append(
        create_conf(
            "127.0.0.1",
            "MRP Device",
            mrp_service(),
            conf.ManualService(
                "dmapid",
                Protocol.DMAP,
                6666,
                {},
                pairing_requirement=PairingRequirement.Mandatory,
            ),
            airplay_service(),
        )
    )
    return scan


@fixture
def dmap_device(scan: AsyncMock = Depends(mock_scan)) -> AsyncMock:
    """Seed scan with a single DMAP-only device."""
    scan.result.append(
        create_conf(
            "127.0.0.1",
            "DMAP Device",
            conf.ManualService(
                "dmapid",
                Protocol.DMAP,
                6666,
                {},
                credentials=None,
                pairing_requirement=PairingRequirement.Mandatory,
            ),
        )
    )
    return scan
