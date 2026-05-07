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

    # Synthesize an object the function belongs to. Syrupy uses
    # `obj.__module__` and `obj.__name__` to derive snapshot keys.
    obj = SimpleNamespace(
        __module__=module.__name__ if module else "tests",
        __name__=func_name,
    )
    item = SimpleNamespace(path=file_path, obj=obj, name=func_name)
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
