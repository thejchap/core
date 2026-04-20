"""Tests for async iterator utility functions."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util.async_iterator import (
    Abort,
    AsyncIteratorReader,
    AsyncIteratorWriter,
)

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


def _read_all(reader: AsyncIteratorReader) -> bytes:
    output = b""
    while chunk := reader.read(500):
        output += chunk
    return output


@test
async def async_iterator_reader(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the async iterator reader."""
    data = b"hello world" * 1000

    async def async_gen() -> AsyncIterator[bytes]:
        for _ in range(10):
            yield data

    reader = AsyncIteratorReader(hass.loop, async_gen())
    expect(await hass.async_add_executor_job(_read_all, reader)).to_equal(data * 10)


@test
async def async_iterator_reader_abort_early(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test abort the async iterator reader."""
    evt = asyncio.Event()

    async def async_gen() -> AsyncIterator[bytes]:
        await evt.wait()
        yield b""

    reader = AsyncIteratorReader(hass.loop, async_gen())
    reader.abort()
    fut = hass.async_add_executor_job(_read_all, reader)
    try:
        await fut
    except Abort:
        pass
    else:
        expect(False).to_be(True)


@test
async def async_iterator_reader_abort_late(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test abort the async iterator reader."""
    evt = asyncio.Event()

    async def async_gen() -> AsyncIterator[bytes]:
        await evt.wait()
        yield b""

    reader = AsyncIteratorReader(hass.loop, async_gen())
    fut = hass.async_add_executor_job(_read_all, reader)
    await asyncio.sleep(0.1)
    reader.abort()
    try:
        await fut
    except Abort:
        pass
    else:
        expect(False).to_be(True)


def _write_all(writer: AsyncIteratorWriter, data: list[bytes]) -> bytes:
    for chunk in data:
        assert writer.write(chunk) == len(chunk)
    assert writer.write(b"") == 0


@test
async def async_iterator_writer(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the async iterator writer."""
    chunk = b"hello world" * 1000
    chunks = [chunk] * 10
    writer = AsyncIteratorWriter(hass.loop)

    fut = hass.async_add_executor_job(_write_all, writer, chunks)

    read = b""
    async for data in writer:
        read += data

    await fut

    expect(read).to_equal(chunk * 10)
    expect(writer.tell()).to_equal(len(read))


@test
async def async_iterator_writer_abort_early(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the async iterator writer."""
    chunk = b"hello world" * 1000
    chunks = [chunk] * 10
    writer = AsyncIteratorWriter(hass.loop)
    writer.abort()

    fut = hass.async_add_executor_job(_write_all, writer, chunks)

    try:
        await fut
    except Abort:
        pass
    else:
        expect(False).to_be(True)


@test
async def async_iterator_writer_abort_late(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the async iterator writer."""
    chunk = b"hello world" * 1000
    chunks = [chunk] * 10
    writer = AsyncIteratorWriter(hass.loop)

    fut = hass.async_add_executor_job(_write_all, writer, chunks)
    await asyncio.sleep(0.1)
    writer.abort()

    try:
        await fut
    except Abort:
        pass
    else:
        expect(False).to_be(True)


@test
async def async_iterator_reader_exhausted(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that read() returns empty bytes after stream exhaustion."""

    async def async_gen() -> AsyncIterator[bytes]:
        yield b"hello"

    reader = AsyncIteratorReader(hass.loop, async_gen())

    def _read_then_read_again() -> bytes:
        data = _read_all(reader)
        # Second read after exhaustion should return b"" immediately.
        assert reader.read(500) == b""
        return data

    expect(await hass.async_add_executor_job(_read_then_read_again)).to_equal(b"hello")
