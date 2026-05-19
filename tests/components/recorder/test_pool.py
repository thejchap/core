"""Test pool."""

import asyncio
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.const import DB_WORKER_PREFIX
from homeassistant.components.recorder.pool import RecorderPool
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def recorder_pool_called_from_event_loop() -> None:
    """Test we raise an exception when calling from the event loop."""
    recorder_and_worker_thread_ids: set[int] = set()
    engine = create_engine(
        "sqlite://",
        poolclass=RecorderPool,
        recorder_and_worker_thread_ids=recorder_and_worker_thread_ids,
    )

    def _raise_on_connect() -> None:
        sessionmaker(bind=engine)().connection()

    async def _run() -> None:
        _raise_on_connect()

    async with expect_raises_async(RuntimeError):
        await _run()


@test
async def recorder_pool(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test RecorderPool gives the same connection in the creating thread."""
    recorder_and_worker_thread_ids: set[int] = set()
    engine = create_engine(
        "sqlite://",
        poolclass=RecorderPool,
        recorder_and_worker_thread_ids=recorder_and_worker_thread_ids,
    )
    get_session = sessionmaker(bind=engine)
    shutdown = False
    connections = []
    add_thread = False

    event = asyncio.Event()

    def _get_connection_twice():
        if add_thread:
            recorder_and_worker_thread_ids.add(threading.get_ident())
        session = get_session()
        connections.append(session.connection().connection.driver_connection)
        session.close()

        if shutdown:
            engine.pool.shutdown()

        session = get_session()
        connections.append(session.connection().connection.driver_connection)
        session.close()
        hass.loop.call_soon_threadsafe(event.set)

    caplog.clear()
    event.clear()
    new_thread = threading.Thread(target=_get_connection_twice)
    new_thread.start()
    await event.wait()
    new_thread.join()
    expect(
        "accesses the database without the database executor" in caplog.text
    ).to_be(True)
    expect(connections[0] != connections[1]).to_be(True)

    add_thread = True
    caplog.clear()
    event.clear()
    new_thread = threading.Thread(target=_get_connection_twice, name=DB_WORKER_PREFIX)
    new_thread.start()
    await event.wait()
    new_thread.join()
    expect(
        "accesses the database without the database executor" not in caplog.text
    ).to_be(True)
    expect(connections[2] == connections[3]).to_be(True)

    caplog.clear()
    event.clear()
    new_thread = threading.Thread(target=_get_connection_twice, name="Recorder")
    new_thread.start()
    await event.wait()
    new_thread.join()
    expect(
        "accesses the database without the database executor" not in caplog.text
    ).to_be(True)
    expect(connections[4] == connections[5]).to_be(True)

    shutdown = True
    caplog.clear()
    event.clear()
    new_thread = threading.Thread(target=_get_connection_twice, name=DB_WORKER_PREFIX)
    new_thread.start()
    await event.wait()
    new_thread.join()
    expect(
        "accesses the database without the database executor" not in caplog.text
    ).to_be(True)
    expect(connections[6] != connections[7]).to_be(True)
