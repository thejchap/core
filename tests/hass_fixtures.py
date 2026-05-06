"""Shared Tryke fixtures for Home Assistant tests.

This module is the lexical-fixture equivalent of the legacy pytest
``conftest.py`` hass-fixture tree. Under Tryke, fixtures are not
inherited via conftest; consumer tests must import the fixtures they
need and wire them explicitly with ``Depends()`` in the test signature.

Minimum viable port — the first pilot slice only touches ``hass``.
Dependencies that are only meaningful in recorder / integration tests
(``mock_recorder_before_hass``, ``hass_fixture_setup`` used as a
recorder-before-hass tripwire, ``request``-driven
``IGNORE_UNCAUGHT_EXCEPTIONS`` bypass) are intentionally omitted here
and will be added back when subsequent slices need them.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from dataclasses import dataclass
import logging
from pathlib import Path
import ssl
import sys
import tempfile
from typing import Any, Self
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture

from homeassistant import block_async_io
from homeassistant.config_entries import ConfigEntryState
import homeassistant.core as ha
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    category_registry as cr,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
    frame,
    issue_registry as ir,
    label_registry as lr,
    translation as translation_helper,
)
from homeassistant.util import dt as dt_util  # noqa: F401  (side effects on import)
from homeassistant.util.async_ import create_eager_task

from .common import (
    MockConfigEntry,
    async_test_home_assistant,
    get_test_config_dir,
    mock_storage,
)
from .test_util.aiohttp import AiohttpClientMocker, mock_aiohttp_client


@fixture
def hass_storage() -> Generator[dict[str, Any]]:
    """Mock the Home Assistant storage layer for the duration of a test."""
    with mock_storage() as stored_data:
        yield stored_data


@fixture
def load_registries() -> bool:
    """Control whether registries are loaded during hass setup.

    Tests that need to suppress registry loading should define their
    own @fixture named ``load_registries`` that returns False and wire
    it via Depends in the hass consumer instead of this one.
    """
    return True


@fixture
def hass_config_dir() -> str:
    """Provide a test config directory."""
    return get_test_config_dir()


@fixture
async def hass(
    load_registries: bool = Depends(load_registries),
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> AsyncGenerator[HomeAssistant]:
    """Create a test instance of Home Assistant.

    Minimum viable port of the legacy ``hass`` fixture: omits the
    recorder tripwire, IGNORE_UNCAUGHT_EXCEPTIONS bypass, and
    fixture_setup signal; those return when their consumers migrate.
    """
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()

    exceptions: list[BaseException] = []

    def exc_handle(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        if orig_exception_handler is not None:
            orig_exception_handler(loop, context)

    async with async_test_home_assistant(
        loop, load_registries, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)

        # Escape hatch for tests that intentionally trigger uncaught loop
        # exceptions (e.g. testing the unhandled-exception traceback path)
        # and want to clear the captured list before the fixture tears
        # down, mirroring the legacy IGNORE_UNCAUGHT_EXCEPTIONS behavior.
        hass_inst._captured_loop_exceptions = exceptions  # type: ignore[attr-defined]

        await translation_helper.async_load_integrations(hass_inst, {ha.DOMAIN})

        yield hass_inst

        loaded_entries = [
            entry
            for entry in hass_inst.config_entries.async_entries()
            if entry.state is ConfigEntryState.LOADED
        ]
        if loaded_entries:
            await asyncio.gather(
                *(
                    create_eager_task(
                        hass_inst.config_entries.async_unload(config_entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for config_entry in loaded_entries
                )
            )

        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        raise ex


@fixture
async def hass_unloaded(
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> AsyncGenerator[HomeAssistant]:
    """Create a hass instance with registries NOT pre-loaded.

    Equivalent to the pytest pattern
    ``@pytest.mark.parametrize("load_registries", [False])``.
    Tests that need to populate hass_storage manually and call
    ``<registry>.async_load(hass)`` themselves should depend on this
    fixture instead of ``hass``.
    """
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()

    exceptions: list[BaseException] = []

    def exc_handle(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        if orig_exception_handler is not None:
            orig_exception_handler(loop, context)

    async with async_test_home_assistant(
        loop, False, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)

        await translation_helper.async_load_integrations(hass_inst, {ha.DOMAIN})

        yield hass_inst

        loaded_entries = [
            entry
            for entry in hass_inst.config_entries.async_entries()
            if entry.state is ConfigEntryState.LOADED
        ]
        if loaded_entries:
            await asyncio.gather(
                *(
                    create_eager_task(
                        hass_inst.config_entries.async_unload(config_entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for config_entry in loaded_entries
                )
            )

        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        raise ex


@fixture
def aioclient_mock() -> Generator[AiohttpClientMocker]:
    """Mock aioclient calls."""
    with mock_aiohttp_client() as mock_session:
        yield mock_session


@fixture
def area_registry(hass: HomeAssistant = Depends(hass)) -> ar.AreaRegistry:
    """Return the area registry from the current hass instance."""
    return ar.async_get(hass)


@fixture
def category_registry(hass: HomeAssistant = Depends(hass)) -> cr.CategoryRegistry:
    """Return the category registry from the current hass instance."""
    return cr.async_get(hass)


@fixture
def device_registry(hass: HomeAssistant = Depends(hass)) -> dr.DeviceRegistry:
    """Return the device registry from the current hass instance."""
    return dr.async_get(hass)


@fixture
def entity_registry(hass: HomeAssistant = Depends(hass)) -> er.EntityRegistry:
    """Return the entity registry from the current hass instance."""
    return er.async_get(hass)


@fixture
def floor_registry(hass: HomeAssistant = Depends(hass)) -> fr.FloorRegistry:
    """Return the floor registry from the current hass instance."""
    return fr.async_get(hass)


@fixture
def issue_registry(hass: HomeAssistant = Depends(hass)) -> ir.IssueRegistry:
    """Return the issue registry from the current hass instance."""
    return ir.async_get(hass)


@fixture
def label_registry(hass: HomeAssistant = Depends(hass)) -> lr.LabelRegistry:
    """Return the label registry from the current hass instance."""
    return lr.async_get(hass)


class LogCapture:
    """Minimum-viable drop-in for ``pytest.LogCaptureFixture``.

    Only the members actually used by ported HA tests are implemented:
    ``text`` for substring assertions, ``records`` for per-record
    inspection, ``set_level`` / ``at_level`` for scoped level control,
    and ``clear`` for resetting between assertions.
    """

    def __init__(self) -> None:
        """Initialize an empty capture."""
        self.records: list[logging.LogRecord] = []
        self._handler = _ListHandler(self.records)
        self._root = logging.getLogger()
        self._prev_level = self._root.level

    @property
    def text(self) -> str:
        """Formatted text of all captured records."""
        return "\n".join(self._handler.format(r) for r in self.records)

    @property
    def messages(self) -> list[str]:
        """Return list of formatted messages (no level/logger prefix)."""
        return [r.getMessage() for r in self.records]

    def set_level(self, level: int | str, logger: str | None = None) -> None:
        """Set the capture level."""
        target = logging.getLogger(logger) if logger else self._root
        target.setLevel(level)

    def at_level(self, level: int | str, logger: str | None = None) -> _AtLevel:
        """Scoped level change, restored on __exit__."""
        return _AtLevel(self, level, logger)

    def clear(self) -> None:
        """Drop all captured records."""
        self.records.clear()

    def get_records(self, when: str) -> list[logging.LogRecord]:
        """Return records for a test phase.

        Tryke does not expose a pytest-style phase model, so all records
        are returned regardless of ``when`` — this mirrors caplog's
        "call" phase which is the only one HA tests actually ask for.
        """
        return list(self.records)


class _ListHandler(logging.Handler):
    """Capture records into an externally-held list."""

    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink
        self.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


class _AtLevel:
    """Context manager for LogCapture.at_level()."""

    def __init__(self, cap: LogCapture, level: int | str, logger: str | None) -> None:
        self._target = logging.getLogger(logger) if logger else logging.getLogger()
        self._level = level
        self._prev: int | None = None

    def __enter__(self) -> Self:
        self._prev = self._target.level
        self._target.setLevel(self._level)
        return self

    def __exit__(self, *exc: object) -> None:
        if self._prev is not None:
            self._target.setLevel(self._prev)


@fixture
def caplog() -> Generator[LogCapture]:
    """Capture log records for the duration of a test."""
    cap = LogCapture()
    root = logging.getLogger()
    prev_level = root.level
    root.setLevel(logging.DEBUG)
    root.addHandler(cap._handler)
    try:
        yield cap
    finally:
        root.removeHandler(cap._handler)
        root.setLevel(prev_level)


@fixture
def freezer() -> Generator[Any]:
    """Drop-in replacement for pytest-freezer's ``freezer`` fixture."""
    from freezegun import freeze_time  # noqa: PLC0415

    with freeze_time() as frozen:
        yield frozen


@fixture
def tmp_path() -> Generator[Path]:
    """Drop-in replacement for pytest's ``tmp_path`` fixture."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@dataclass
class Captured:
    """Captured stdout/stderr output."""

    out: str
    err: str


class CapFd:
    """Python-level capture of ``sys.stdout`` / ``sys.stderr``.

    Named for parity with pytest's ``capfd`` and usable as a drop-in by
    ported tests. The underlying mechanism is ``sys.stdout``/``sys.stderr``
    reassignment rather than fd-level ``dup2`` because Tryke's own
    test-output capture replaces ``sys.stderr`` before the fixture runs;
    an fd-level dup2 would land in Tryke's capture, not ours. This
    means ``CapFd`` does not catch writes from subprocesses or C
    extensions that bypass ``sys.*``. The HA tests that use this fixture
    only exercise Python-level ``print(..., file=sys.stderr)``.
    """

    def __init__(self) -> None:
        """Initialize with empty buffers and no saved streams."""
        self._out_buf = _StringSink()
        self._err_buf = _StringSink()
        self._saved_out: Any = None
        self._saved_err: Any = None

    def start(self) -> None:
        """Redirect ``sys.stdout`` and ``sys.stderr`` to in-memory buffers."""
        self._saved_out = sys.stdout
        self._saved_err = sys.stderr
        sys.stdout = self._out_buf  # type: ignore[assignment]
        sys.stderr = self._err_buf  # type: ignore[assignment]

    def stop(self) -> None:
        """Restore the original ``sys.stdout`` / ``sys.stderr``."""
        sys.stdout = self._saved_out
        sys.stderr = self._saved_err

    def readouterr(self) -> Captured:
        """Return captured stdout/stderr and clear the buffers."""
        out = self._out_buf.drain()
        err = self._err_buf.drain()
        return Captured(out=out, err=err)


class _StringSink:
    """Minimal text sink matching the ``sys.stderr`` write interface."""

    def __init__(self) -> None:
        self._parts: list[str] = []

    def write(self, s: str) -> int:
        self._parts.append(s)
        return len(s)

    def flush(self) -> None:
        return None

    def isatty(self) -> bool:
        return False

    def drain(self) -> str:
        value = "".join(self._parts)
        self._parts.clear()
        return value


@fixture
def disable_block_async_io() -> Generator[None]:
    """Restore any methods patched by block_async_io after the test."""
    yield
    calls = block_async_io._BLOCKED_CALLS.calls
    for blocking_call in calls:
        setattr(
            blocking_call.object, blocking_call.function, blocking_call.original_func
        )
    calls.clear()


@fixture
def capfd() -> Generator[CapFd]:
    """Drop-in replacement for pytest's ``capfd`` fixture."""
    cap = CapFd()
    cap.start()
    try:
        yield cap
    finally:
        cap.stop()


@fixture
def mock_bluetooth_adapters() -> Generator[None]:
    """Mock bluetooth adapters so the bluetooth integration can be set up."""
    with (
        patch("habluetooth.util.recover_adapter"),
        patch("bluetooth_auto_recovery.recover_adapter"),
        patch("bluetooth_adapters.systems.platform.system", return_value="Linux"),
        patch("bluetooth_adapters.systems.linux.LinuxAdapters.refresh"),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.adapters",
            {
                "hci0": {
                    "address": "00:00:00:00:00:01",
                    "hw_version": "usb:v1D6Bp0246d053F",
                    "passive_scan": False,
                    "sw_version": "homeassistant",
                    "manufacturer": "ACME",
                    "product": "Bluetooth Adapter 5.0",
                    "product_id": "aa01",
                    "vendor_id": "cc01",
                },
            },
        ),
    ):
        yield


@fixture
def mock_bleak_scanner_start() -> Generator[MagicMock]:
    """Mock starting the bleak scanner so the bluetooth manager can come up."""
    from habluetooth import (  # noqa: PLC0415
        manager as bluetooth_manager,
        scanner as bluetooth_scanner,
    )

    # We patch out start so the scanner never actually opens an adapter.
    # The fixture exits before EVENT_HOMEASSISTANT_STOP fires the stop call,
    # so detach stop too.
    bluetooth_scanner.OriginalBleakScanner.stop = AsyncMock()  # type: ignore[assignment]

    mock_mgmt_bluetooth_ctl = Mock()
    mock_mgmt_bluetooth_ctl.setup = AsyncMock(return_value=None)

    with (
        patch.object(
            bluetooth_scanner.OriginalBleakScanner,
            "start",
        ) as mock_bleak_scanner_start,
        patch.object(bluetooth_scanner, "HaScanner"),
        patch.object(
            bluetooth_manager, "MGMTBluetoothCtl", return_value=mock_mgmt_bluetooth_ctl
        ),
    ):
        yield mock_bleak_scanner_start


@fixture
async def enable_bluetooth(
    hass: HomeAssistant = Depends(hass),
    _bleak: MagicMock = Depends(mock_bleak_scanner_start),
    _adapters: None = Depends(mock_bluetooth_adapters),
) -> AsyncGenerator[None]:
    """Set up the bluetooth integration with adapters and scanner mocked."""
    entry = MockConfigEntry(domain="bluetooth", unique_id="00:00:00:00:00:01")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@fixture
def mock_network() -> Generator[None]:
    """Patch network adapter discovery so tests that touch aiohttp-session

    construction (which pulls the zeroconf resolver, which queries the
    network adapter list) don't blow up on a minimal hass fixture that
    has no ``network`` integration loaded. Also patches the aiohttp
    resolver factory so integrations that call
    ``async_get_clientsession(hass)`` during a config flow don't attempt
    to spin up a real zeroconf instance whose background threads outlive
    the test event loop.
    """
    from aiohttp.resolver import AsyncResolver  # noqa: PLC0415

    def _make_resolver(*_args: Any, **_kwargs: Any) -> AsyncResolver:
        return AsyncResolver()

    with (
        patch(
            "homeassistant.components.network.util.ifaddr.get_adapters",
            return_value=[
                Mock(
                    nice_name="eth0",
                    ips=[Mock(is_IPv6=False, ip="10.10.10.10", network_prefix=24)],
                    index=0,
                )
            ],
        ),
        patch(
            "homeassistant.components.network.async_get_loaded_adapters",
            return_value=[
                {
                    "auto": True,
                    "default": True,
                    "enabled": True,
                    "index": 0,
                    "ipv4": [{"address": "10.10.10.10", "network_prefix": 24}],
                    "ipv6": [],
                    "name": "eth0",
                }
            ],
        ),
        patch(
            "homeassistant.components.network.util.async_get_source_ip",
            return_value="10.10.10.10",
        ),
        patch(
            "homeassistant.helpers.aiohttp_client._async_make_resolver",
            side_effect=_make_resolver,
        ),
    ):
        yield


# Aliased so consumer modules can `from tests.hass_fixtures import ClientSessionGenerator`
# without pulling tests.typing's pytest hooks (which conflict with tryke discovery).
type ClientSessionGenerator = Callable[..., Coroutine[Any, Any, Any]]


@fixture
async def aiohttp_client() -> AsyncGenerator[ClientSessionGenerator]:
    """Test-client factory bound to the running event loop.

    Mirror of the pytest ``aiohttp_client`` fixture used by HA tests, but
    without the third-party ``pytest-aiohttp`` plugin: the fixture
    creates aiohttp test clients/servers and tears them down on exit.
    """
    from aiohttp.test_utils import (  # noqa: PLC0415
        BaseTestServer,
        TestClient,
        TestServer,
    )
    from aiohttp.web import Application  # noqa: PLC0415

    loop = asyncio.get_running_loop()
    clients: list[TestClient] = []

    async def go(
        param: Any,
        /,
        *args: Any,
        server_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> TestClient:
        client: TestClient
        if isinstance(param, Application):
            server_kwargs = server_kwargs or {}
            server = TestServer(param, loop=loop, **server_kwargs)
            server.app._router.freeze = lambda: None  # noqa: SLF001
            client = TestClient(server, loop=loop, **kwargs)
        elif isinstance(param, BaseTestServer):
            client = TestClient(param, loop=loop, **kwargs)
        else:
            raise TypeError(f"Unknown argument type: {type(param)!r}")

        await client.start_server()
        clients.append(client)
        return client

    try:
        yield go
    finally:
        while clients:
            await clients.pop().close()


@fixture
def hass_client_no_auth(
    hass: HomeAssistant = Depends(hass),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client),
) -> ClientSessionGenerator:
    """Return an unauthenticated HTTP client for the hass test app."""

    async def client():
        return await aiohttp_client(hass.http.app)

    return client


@fixture
def current_request() -> Generator[MagicMock]:
    """Mock the helpers.http current_request context-var lookup."""
    from aiohttp.test_utils import make_mocked_request  # noqa: PLC0415

    with patch("homeassistant.helpers.http.current_request") as mock_request_context:
        mocked_request = make_mocked_request(
            "GET",
            "/some/request",
            headers={"Host": "example.com"},
            sslcontext=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        )
        mock_request_context.get.return_value = mocked_request
        yield mock_request_context


@fixture
def current_request_with_host(
    current_request: MagicMock = Depends(current_request),
) -> None:
    """Mock current request with a host header that OAuth2 flows expect."""
    import multidict  # noqa: PLC0415

    from homeassistant.helpers import config_entry_oauth2_flow  # noqa: PLC0415

    new_headers = multidict.CIMultiDict(current_request.get.return_value.headers)
    new_headers[config_entry_oauth2_flow.HEADER_FRONTEND_BASE] = "https://example.com"
    current_request.get.return_value = current_request.get.return_value.clone(
        headers=new_headers
    )
