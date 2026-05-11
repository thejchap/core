"""Tryke helpers for HA test ports — async raises, zeroconf mocks, etc.

Lives next to ``hass_fixtures`` but kept separate so contributors can grep
for the helper names individually. Import as needed:

    from tests.hass_tryke_helpers import (
        expect_raises_async,
        mock_async_zeroconf,
        requests_mock_session,
        snapshot,
    )
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
import inspect
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import requests_mock as rm_lib
from syrupy.assertion import SnapshotAssertion
from syrupy.location import PyTestLocation
from tryke import fixture

from .syrupy import HomeAssistantSnapshotExtension


@asynccontextmanager
async def expect_raises_async(
    error_type: type[BaseException],
    *,
    match: str | None = None,
) -> AsyncGenerator[None]:
    """Async equivalent of ``expect(callable).to_raise(...)``.

    Tryke 0.0.27's ``to_raise`` only handles synchronous callables. Use
    this around an inline ``await``::

        async with expect_raises_async(ValueError, match=r"bad"):
            await thing.do_it()
    """
    raised: BaseException | None = None
    try:
        yield
    except BaseException as exc:  # noqa: BLE001
        raised = exc

    if not isinstance(raised, error_type):
        raise AssertionError(
            f"Expected {error_type.__name__} to be raised, "
            f"got {type(raised).__name__ if raised else 'None'}"
        )
    if match is not None and not re.search(match, str(raised)):
        raise AssertionError(f"Expected match {match!r} in {raised!r}")


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Patch the async zeroconf instance so flows that consume it don't hit the network.

    pytest-aiohttp / pytest-syrupy adjacent integrations (apple_tv, hue,
    etc.) consume ``async_zeroconf`` at flow init time. Mock the entire
    ``zeroconf.HaAsyncZeroconf`` rather than fight with the real
    implementation.
    """
    with patch(
        "homeassistant.components.zeroconf.async_get_async_instance",
        new=AsyncMock(),
    ) as zc:
        zc.return_value = MagicMock()
        zc.return_value.async_register_service = AsyncMock()
        zc.return_value.async_unregister_service = AsyncMock()
        yield zc


@fixture
def requests_mock_session() -> Generator[rm_lib.Mocker]:
    """Drop-in for the pytest-requests-mock plugin's ``requests_mock`` fixture.

    Wraps ``requests_mock.Mocker()`` (the library context manager) as a
    ``@fixture`` so consumer tests can ``Depends(requests_mock_session)``
    and use it the same way they'd use the pytest plugin's autouse.
    """
    with rm_lib.Mocker() as m:
        yield m


@contextmanager
def patch_requests_mock(*registrations: tuple[str, str, dict[str, Any]]) -> Generator[rm_lib.Mocker]:
    """Inline ``with`` form for one-off requests-mock setups.

    Each ``registrations`` entry is ``(method, url, response_kwargs)``::

        with patch_requests_mock(
            ("GET", "https://example.com/api", {"json": {"ok": True}}),
        ) as m:
            await client.fetch()
    """
    with rm_lib.Mocker() as m:
        for method, url, kwargs in registrations:
            m.register_uri(method, url, **kwargs)
        yield m


# --- OAuth2 application credentials helper --------------------------------


async def setup_application_credentials(
    hass: Any,
    domain: str,
    client_id: str = "client_id",
    client_secret: str = "client_secret",
    auth_implementation: str | None = None,
) -> None:
    """Set up the OAuth2 application_credentials chain for an integration's tests.

    Replacement for the ``setup_credentials`` autouse fixture in pytest
    integration conftests (e.g. ``tests/components/google_mail/conftest.py``,
    ``tests/components/fitbit/conftest.py``). Initialises the
    ``application_credentials`` component and imports a client credential
    so OAuth2 flows can complete.

    Usage in a per-integration ``_fixtures.py``::

        from tryke import Depends, fixture
        from tests.hass_fixtures import hass as hass_fixture
        from tests.hass_tryke_helpers import setup_application_credentials
        from homeassistant.components.<int>.const import DOMAIN

        @fixture
        async def setup_credentials(
            hass: HomeAssistant = Depends(hass_fixture),
        ) -> None:
            await setup_application_credentials(
                hass, DOMAIN, "client_id", "client_secret", "auth_impl_name"
            )

    Then have ``_trigger_executor`` (or each test) ``Depends(setup_credentials)``.
    """
    from homeassistant.components.application_credentials import (  # noqa: PLC0415
        DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
        ClientCredential,
        async_import_client_credential,
    )
    from homeassistant.setup import async_setup_component  # noqa: PLC0415

    if APPLICATION_CREDENTIALS_DOMAIN not in hass.config.components:
        assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        domain,
        ClientCredential(client_id, client_secret),
        auth_implementation,
    )


def make_oauth_token(
    *,
    access_token: str = "mock-access-token",
    refresh_token: str = "mock-refresh-token",
    scopes: list[str] | None = None,
    expires_in: int = 3600,
    token_type: str = "Bearer",
) -> dict[str, Any]:
    """Construct an OAuth2 token dict for a MockConfigEntry's ``data['token']``.

    Mirrors the ``token_entry`` / ``server_access_token`` fixtures across HA's
    OAuth2 integration tests. ``expires_at`` is computed from ``expires_in``
    relative to the current time so the token doesn't appear pre-expired.
    """
    import time as _time  # noqa: PLC0415

    token: dict[str, Any] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": token_type,
        "expires_at": _time.time() + expires_in,
        "expires_in": expires_in,
    }
    if scopes is not None:
        token["scope"] = " ".join(scopes)
    return token


# --- respx async HTTP mock helpers ----------------------------------------


@asynccontextmanager
async def respx_mock_session(
    *,
    assert_all_called: bool = False,
    assert_all_mocked: bool = True,
) -> AsyncGenerator[Any]:
    """Async context manager wrapping respx.mock for HTTPX-based integration tests.

    Use inside ``async with`` to register HTTPX route mocks::

        async with respx_mock_session() as respx_mock:
            respx_mock.get("https://example.com/api").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )
            # ... test body ...

    This replaces the ``respx.mock`` pytest plugin's autouse fixture. Set
    ``assert_all_called=True`` to fail the test if any registered route was
    never hit.
    """
    import respx as _respx  # noqa: PLC0415

    with _respx.mock(
        assert_all_called=assert_all_called,
        assert_all_mocked=assert_all_mocked,
    ) as m:
        yield m


# --- entity registry helpers ----------------------------------------------


@fixture
def entity_registry_enabled_by_default() -> Generator[Any]:
    """Force every integration entity to be enabled-by-default.

    Replacement for the ``entity_registry_enabled_by_default`` autouse
    fixture in many sibling test files. Without it, integrations whose
    entity descriptions set ``entity_registry_enabled_default=False``
    (legacy / niche sensors) skip entity creation, breaking
    ``snapshot_platform`` and entity-presence assertions.
    """
    from unittest.mock import patch as _patch  # noqa: PLC0415

    with _patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ):
        yield


# --- supervisor_client helpers --------------------------------------------


def make_supervisor_client_mock(
    *,
    addons_installed: list[str] | None = None,
    os_info: dict[str, Any] | None = None,
) -> Any:
    """Build a minimal `aiohasupervisor` client mock for hassio-dependent tests.

    Mirrors the supervisor_client mock pattern in
    ``tests/components/homeassistant_connect_zbt2/_fixtures.py`` but as a
    factory consumable by any integration whose tests bridge through the
    Home Assistant Supervisor (otbr, homeassistant_green/sky_connect/yellow,
    music_assistant via hassio, etc.).

    Returns a ``MagicMock`` shaped like ``aiohasupervisor.SupervisorClient``
    with the ``addons``, ``os``, and ``store`` namespaces wired enough for
    the most common test paths. Tests can extend the returned object
    in-place before passing it through ``patch(..., return_value=client)``.
    """
    from unittest.mock import AsyncMock, MagicMock  # noqa: PLC0415

    client = MagicMock()
    addons_list = addons_installed or []

    # addons namespace
    client.addons = MagicMock()
    client.addons.list = AsyncMock(
        return_value=MagicMock(addons=addons_list)
    )
    client.addons.addon_info = AsyncMock(
        return_value=MagicMock(installed=False, available=True, version="1.0.0")
    )
    client.addons.start_addon = AsyncMock(return_value=None)
    client.addons.stop_addon = AsyncMock(return_value=None)
    client.addons.uninstall_addon = AsyncMock(return_value=None)

    # store namespace
    client.store = MagicMock()
    client.store.addon_store_info = AsyncMock(
        return_value=MagicMock(installed=False, available=True, version="1.0.0")
    )
    client.store.install_addon = AsyncMock(return_value=None)

    # os namespace
    client.os = MagicMock()
    info = os_info or {
        "version": "12.0",
        "version_latest": "12.0",
        "update_available": False,
        "board": "generic-x86-64",
        "boot": "A",
    }
    client.os.info = AsyncMock(return_value=MagicMock(**info))

    return client


# --- mqtt_mock helpers ----------------------------------------------------


async def setup_mqtt_mock(
    hass: Any,
    config_entry_data: dict[str, Any] | None = None,
    config_entry_options: dict[str, Any] | None = None,
) -> Any:
    """Set up an MQTT mock for tests, returning the mocked HA MQTT client.

    Replacement for the ``mqtt_mock`` fixture in ``tests/conftest.py``.
    Initialises the MQTT integration with a mocked paho client and a
    pre-configured config entry, returns the mock that tests assert on.

    Usage in a per-integration ``_fixtures.py``::

        from tryke import Depends, fixture
        from tests.hass_fixtures import hass as hass_fixture
        from tests.hass_tryke_helpers import setup_mqtt_mock

        @fixture
        async def mqtt_mock(
            hass: HomeAssistant = Depends(hass_fixture),
        ):
            return await setup_mqtt_mock(hass)

    Skips the real-MQTT-instance verification from the conftest fixture
    (those checks are integration-internal). The returned mock supports
    ``async_publish`` / ``async_subscribe`` / ``connected`` / ``mock_calls``
    for assertion patterns.

    The paho-client mock wires ``on_publish`` / ``on_subscribe`` /
    ``on_unsubscribe`` callbacks via ``hass.loop.call_soon`` (mirroring the
    pytest ``mqtt_client_mock`` fixture in ``tests/conftest.py``) so the
    integration's ``_pending_operations`` mid-future bookkeeping resolves
    each publish/subscribe round-trip. Without this, repeated publishes
    raise ``KeyError`` when the integration tries to delete the same
    pending-operation mid twice.
    """
    from unittest.mock import MagicMock, Mock, patch  # noqa: PLC0415

    from homeassistant.components import mqtt  # noqa: PLC0415
    from homeassistant.config_entries import ConfigEntryState  # noqa: PLC0415
    from homeassistant.core import callback as _ha_callback  # noqa: PLC0415
    from homeassistant.setup import async_setup_component  # noqa: PLC0415

    from .common import (  # noqa: PLC0415
        MockConfigEntry,
        MockMqttReasonCode,
        async_fire_mqtt_message,
    )

    if config_entry_data is None:
        config_entry_data = {
            mqtt.CONF_BROKER: "mock-broker",
            mqtt.CONF_PROTOCOL: "5",
        }
    if config_entry_options is None:
        config_entry_options = {mqtt.CONF_BIRTH_MESSAGE: {}}

    # Per-publish/subscribe message-id counter. The integration's
    # ``_pending_operations`` dict keys on this and deletes the entry once
    # the matching ``on_publish``/``on_subscribe`` callback fires, so we
    # must hand out a fresh mid for each call (NOT a constant).
    _mid: int = 0

    def _next_mid() -> int:
        nonlocal _mid
        _mid += 1
        return _mid

    class _FakePublishInfo:
        """Stand-in for ``paho.mqtt.client.MQTTMessageInfo``."""

        def __init__(self, mid: int) -> None:
            self.mid = mid
            self.rc = 0

        def is_published(self) -> bool:
            return True

    # Build a paho-client mock with the methods MQTT integration calls.
    paho_client_mock = MagicMock()
    paho_client_mock.connect = MagicMock(return_value=0)
    paho_client_mock.loop_start = MagicMock()
    paho_client_mock.loop_stop = MagicMock()
    paho_client_mock.disconnect = MagicMock()
    paho_client_mock.reconnect = MagicMock()
    paho_client_mock.is_connected = MagicMock(return_value=True)
    paho_client_mock.tls_set = MagicMock()
    paho_client_mock.tls_insecure_set = MagicMock()
    paho_client_mock.username_pw_set = MagicMock()
    paho_client_mock.will_set = MagicMock()
    paho_client_mock.connect_async = MagicMock()
    paho_client_mock.loop_read = MagicMock(return_value=0)

    # publish/subscribe/unsubscribe must schedule the matching ack
    # callback so the integration's mid-future resolves. ``call_soon``
    # mimics the asynchronous broker round-trip — by the time the
    # integration awaits the future, the loop has run the callback and
    # the future is set.
    @_ha_callback
    def _publish_side_effect(
        topic: str, payload: Any, qos: int, retain: bool
    ) -> _FakePublishInfo:
        async_fire_mqtt_message(hass, topic, payload or b"", qos, retain)
        mid = _next_mid()
        hass.loop.call_soon(
            paho_client_mock.on_publish,
            Mock(),
            0,
            mid,
            MockMqttReasonCode(),
            None,
        )
        return _FakePublishInfo(mid)

    def _subscribe_side_effect(topic: str, qos: int = 0) -> tuple[int, int]:
        mid = _next_mid()
        hass.loop.call_soon(
            paho_client_mock.on_subscribe,
            Mock(),
            0,
            mid,
            [MockMqttReasonCode()],
            None,
        )
        return (0, mid)

    def _unsubscribe_side_effect(topic: str) -> tuple[int, int]:
        mid = _next_mid()
        hass.loop.call_soon(
            paho_client_mock.on_unsubscribe,
            Mock(),
            0,
            mid,
            [MockMqttReasonCode()],
            None,
        )
        return (0, mid)

    paho_client_mock.publish = MagicMock(side_effect=_publish_side_effect)
    paho_client_mock.subscribe = MagicMock(side_effect=_subscribe_side_effect)
    paho_client_mock.unsubscribe = MagicMock(side_effect=_unsubscribe_side_effect)

    entry = MockConfigEntry(
        data=config_entry_data,
        options=config_entry_options,
        domain=mqtt.DOMAIN,
        title="MQTT",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
        return_value=paho_client_mock,
    ):
        assert await async_setup_component(hass, mqtt.DOMAIN, {})
        await hass.async_block_till_done()

        # Drive the on_connect callback once so the integration's
        # connection-state future resolves and ``connected = True`` —
        # mirrors the dev ``_setup_mqtt_entry`` behavior.
        paho_client_mock.on_connect(
            paho_client_mock, None, 0, MockMqttReasonCode()
        )
        await hass.async_block_till_done()

    # Return the mqtt component's HA-side client (used by tests for
    # async_publish assertions etc.). If setup didn't fully wire, return the
    # paho mock so consumer tests at least have something to assert against.
    if entry.state is ConfigEntryState.LOADED:
        return entry.runtime_data
    return paho_client_mock


# --- recorder_mock helper -------------------------------------------------


async def setup_recorder_mock(
    hass: Any,
    add_config: dict[str, Any] | None = None,
    *,
    db_url: str = "sqlite://",
) -> Any:
    """Set up an in-memory recorder instance for tests.

    Replacement for the ``recorder_mock`` fixture in
    ``tests/conftest.py``. Initialises the recorder component with an
    in-memory SQLite database (default), waits for setup, and returns the
    `Recorder` instance.

    Usage in a per-integration ``_fixtures.py``::

        from tryke import Depends, fixture
        from tests.hass_fixtures import hass as hass_fixture
        from tests.hass_tryke_helpers import setup_recorder_mock

        @fixture
        async def recorder_mock(
            hass: HomeAssistant = Depends(hass_fixture),
        ):
            return await setup_recorder_mock(hass)

    Then have ``_trigger_executor`` (or each test) ``Depends(recorder_mock)``.

    Notes:
    - Skips heavy diagnostic wrapping (no debug session scope, no nightly
      purge tracking). For tests that need those, extend in `_fixtures.py`.
    - `commit_interval` defaults to 0 so writes flush immediately, matching
      the conftest fixture.
    """
    from unittest.mock import patch as _patch  # noqa: PLC0415

    from homeassistant.components import recorder  # noqa: PLC0415
    from homeassistant.helpers import recorder as recorder_helper  # noqa: PLC0415
    from homeassistant.setup import async_setup_component  # noqa: PLC0415

    config = dict(add_config) if add_config else {}
    if recorder.CONF_DB_URL not in config:
        config[recorder.CONF_DB_URL] = db_url
        if recorder.CONF_COMMIT_INTERVAL not in config:
            config[recorder.CONF_COMMIT_INTERVAL] = 0

    with _patch(
        "homeassistant.components.recorder.ALLOW_IN_MEMORY_DB", True
    ):
        if recorder.DOMAIN not in hass.data:
            recorder_helper.async_initialize_recorder(hass)
        setup_result = await async_setup_component(
            hass, recorder.DOMAIN, {recorder.DOMAIN: config}
        )
        assert setup_result is True
        assert recorder.DOMAIN in hass.config.components

    instance = hass.data[recorder.DATA_INSTANCE]
    # Block until the recorder thread has settled (mirrors
    # async_recorder_block_till_done in tests/components/recorder/common.py).
    await hass.async_block_till_done()
    if hasattr(instance, "async_block_till_done"):
        await instance.async_block_till_done()
    return instance


# --- syrupy snapshot fixture ----------------------------------------------
#
# Syrupy's pytest plugin builds a SnapshotAssertion from
#   - request.node (a pytest.Item) for PyTestLocation
#   - request.session.config (with ._syrupy SnapshotSession + .option.update_snapshots)
#
# Tryke has neither. We synthesise just enough of each that
# `snapshot == data` works for read-only comparison against `.ambr` files.
# Update mode and unused-snapshot detection are out of scope (use pytest +
# `--snapshot-update` for those, then run tryke read-only against the result).


class _StubSession:
    """Minimal stand-in for ``SnapshotSession``.

    Implements only the methods ``SnapshotAssertion`` actually invokes
    during ``__eq__`` / ``_assert``: ``recall_snapshot`` and the
    ``update_snapshots`` property. Write paths
    (``_queue_snapshot_write`` etc.) are silently no-op'd.
    """

    def __init__(self) -> None:
        self._queued_snapshot_writes: dict[str, dict[Any, Any]] = defaultdict(dict)
        self._assertions: list[Any] = []
        # Minimal pytest_session.config.option.update_snapshots
        self.pytest_session = SimpleNamespace(
            config=SimpleNamespace(option=SimpleNamespace(update_snapshots=False))
        )

    def register_request(self, assertion: SnapshotAssertion) -> None:
        self._assertions.append(assertion)

    def recall_snapshot(
        self,
        extension: Any,
        test_location: PyTestLocation,
        index: Any,
    ) -> Any:
        return extension.read_snapshot(
            test_location=test_location, index=index, session_id=str(id(self))
        )

    def queue_snapshot_write(self, *args: Any, **kwargs: Any) -> None:
        # No-op: tryke runs read-only. Use pytest --snapshot-update to
        # regenerate `.ambr` files first.
        return None

    @property
    def update_snapshots(self) -> bool:
        return False

    @property
    def warn_unused_snapshots(self) -> bool:
        return False


def _stub_test_location(caller_frame: Any) -> PyTestLocation:
    """Build a PyTestLocation from an inspected stack frame.

    Walks one level up to find the running test function. Tryke's @test
    wraps the function, so we synthesize an Item-like object whose
    ``.path`` is the test file, ``.obj`` is the function (so syrupy can
    read ``__module__`` and ``__name__``), and ``.name`` is the test name.
    """
    func_name = caller_frame.f_code.co_name
    file_path = Path(caller_frame.f_code.co_filename).resolve()
    module = inspect.getmodule(caller_frame)

    # Tryke's @test convention strips the `test_` prefix from function
    # names, but existing .ambr files (generated under pytest) key on
    # the `test_<name>` form. Add the prefix here so shim'd tests can
    # match snapshots produced by pytest without regenerating them.
    pytest_compatible_name = (
        func_name if func_name.startswith("test_") else f"test_{func_name}"
    )

    obj = SimpleNamespace(
        __module__=module.__name__ if module else "tests",
        __name__=pytest_compatible_name,
    )
    nodeid = f"{file_path}::{pytest_compatible_name}"
    item = SimpleNamespace(
        path=file_path,
        obj=obj,
        name=pytest_compatible_name,
        nodeid=nodeid,
        originalname=pytest_compatible_name,
    )
    return PyTestLocation(item=item)  # type: ignore[arg-type]


@fixture
def snapshot() -> Generator[SnapshotAssertion]:
    """Drop-in for syrupy's ``snapshot`` fixture, wired with HA's extension.

    Read-only — fails on missing snapshots rather than auto-creating them.
    Run pytest with ``--snapshot-update`` to (re)generate ``.ambr`` files,
    then re-run tryke to assert against them.
    """
    session = _StubSession()
    # PyTestLocation needs the calling test's frame. The fixture is
    # consumed from a tryke @test, so the caller's caller is the test.
    frame = inspect.currentframe()
    test_frame = frame.f_back if frame else None
    while test_frame is not None and "tryke" in (test_frame.f_code.co_filename or ""):
        test_frame = test_frame.f_back
    if test_frame is None:
        raise RuntimeError(
            "snapshot fixture: could not locate the test frame for PyTestLocation"
        )

    assertion = SnapshotAssertion(
        update_snapshots=False,
        extension_class=HomeAssistantSnapshotExtension,
        test_location=_stub_test_location(test_frame),
        session=session,  # type: ignore[arg-type]
    )
    session.register_request(assertion)
    yield assertion
