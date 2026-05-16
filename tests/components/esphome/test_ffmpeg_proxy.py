"""Tests for ffmpeg proxy view."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
import io
import logging
import os
import tempfile
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.request import pathname2url
import wave

from aiohttp import client_exceptions
import mutagen
from tryke import Depends, expect, fixture, test

from homeassistant.components import esphome
from homeassistant.components.esphome.ffmpeg_proxy import (
    _MAX_STDERR_LINES,
    async_create_proxy_url,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    load_homeassistant as load_homeassistant_fixture,
    mock_tts_cache_dir as mock_tts_cache_dir_fixture,
)

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import ClientSessionGenerator

FFMPEG_PROXY = "homeassistant.components.esphome.ffmpeg_proxy"


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _tts: None = Depends(mock_tts_cache_dir_fixture),
    _homeassistant: None = Depends(load_homeassistant_fixture),
) -> int:
    return 0


def _write_silence(filename: str, length: int) -> None:
    """Write silence to a file."""
    with wave.open(filename, "wb") as wav_file:
        wav_file.setframerate(16000)
        wav_file.setsampwidth(2)
        wav_file.setnchannels(1)
        wav_file.writeframes(bytes(16000 * 2 * length))  # length s


@test
async def async_create_proxy_url_test(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that async_create_proxy_url returns the correct format."""
    expect(await async_setup_component(hass, "esphome", {})).to_be(True)

    device_id = "test-device"
    convert_id = "test-id"
    media_format = "flac"
    media_url = "http://127.0.0.1/test.mp3"
    proxy_url = f"/api/esphome/ffmpeg_proxy/{device_id}/{convert_id}.{media_format}"

    with patch(
        "homeassistant.components.esphome.ffmpeg_proxy.secrets.token_urlsafe",
        return_value=convert_id,
    ):
        expect(
            async_create_proxy_url(hass, device_id, media_url, media_format)
        ).to_equal(proxy_url)


@test
async def proxy_view(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test proxy HTTP view for converting audio."""
    device_id = "1234"

    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".wav") as temp_file:
        _write_silence(temp_file.name, 1)
        wav_file = temp_file.name

        await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
        client = await hass_client()

        wav_url = pathname2url(wav_file)
        convert_id = "test-id"
        url = f"/api/esphome/ffmpeg_proxy/{device_id}/{convert_id}.mp3"

        # Should fail because we haven't allowed the URL yet
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.NOT_FOUND)

        # Allow the URL
        with patch(
            "homeassistant.components.esphome.ffmpeg_proxy.secrets.token_urlsafe",
            return_value=convert_id,
        ):
            expect(
                async_create_proxy_url(
                    hass,
                    device_id,
                    wav_url,
                    media_format="mp3",
                    rate=22050,
                    channels=2,
                )
            ).to_equal(url)

        # Requesting the wrong media format should fail
        wrong_url = f"/api/esphome/ffmpeg_proxy/{device_id}/{convert_id}.flac"
        req = await client.get(wrong_url)
        expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)

        # Correct URL
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)

        mp3_data = await req.content.read()

        # Verify conversion
        with io.BytesIO(mp3_data) as mp3_io:
            mp3_file = mutagen.File(mp3_io)
            expect(mp3_file.info.sample_rate).to_equal(22050)
            expect(mp3_file.info.channels).to_equal(2)

            # About a second, but not exact
            expect(round(mp3_file.info.length, 0)).to_equal(1)


@test
async def ffmpeg_file_doesnt_exist(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test ffmpeg conversion with a file that doesn't exist."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    # Try to convert a file that doesn't exist
    url = async_create_proxy_url(hass, device_id, "missing-file", media_format="mp3")
    req = await client.get(url)

    # The HTTP status is OK because the ffmpeg process started, but no data is
    # returned.
    expect(req.status).to_equal(HTTPStatus.OK)
    mp3_data = await req.content.read()
    expect(bool(mp3_data)).to_be(False)

    # ffmpeg failure should be logged at error level
    expect("FFmpeg conversion failed for device" in caplog.text).to_be(True)
    expect(device_id in caplog.text).to_be(True)


@test
async def ffmpeg_error_stderr_truncated(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that ffmpeg stderr output is truncated in error logs."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    total_lines = _MAX_STDERR_LINES + 50
    stderr_lines_data = [f"stderr line {i}\n".encode() for i in range(total_lines)] + [
        b""
    ]

    async def _stdout_read(_size: int = -1) -> bytes:
        """Yield to event loop so stderr collector can run, then return EOF."""
        await asyncio.sleep(0)
        return b""

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = AsyncMock(side_effect=stderr_lines_data)
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        await req.content.read()

    # Should log an error with stderr content
    expect("FFmpeg conversion failed for device" in caplog.text).to_be(True)

    # Find the error message to verify truncation.
    # We can't just check caplog.text because lines beyond the limit
    # are still present at debug level from _collect_ffmpeg_stderr.
    error_message = next(
        r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
        and "FFmpeg conversion failed" in r.getMessage()
    )

    total_lines = _MAX_STDERR_LINES + 50

    # The last _MAX_STDERR_LINES lines should be present
    for i in range(total_lines - _MAX_STDERR_LINES, total_lines):
        expect(f"stderr line {i}" in error_message).to_be(True)

    # Early lines that were evicted should not be in the error log
    expect("stderr line 0" not in error_message).to_be(True)


@test
async def ffmpeg_error_redacts_sensitive_urls(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that sensitive query params are redacted in error logs."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    sensitive_url = (
        "https://example.com/api/tts?authSig=secret123&token=abc456&other=keep"
    )
    stderr_lines_data = [
        f"Error opening input file {sensitive_url}\n".encode(),
        b"",
    ]

    async def _stdout_read(_size: int = -1) -> bytes:
        await asyncio.sleep(0)
        return b""

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = AsyncMock(side_effect=stderr_lines_data)
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        await req.content.read()

    error_message = next(
        r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
        and "FFmpeg conversion failed" in r.getMessage()
    )

    expect("authSig=REDACTED" in error_message).to_be(True)
    expect("token=REDACTED" in error_message).to_be(True)
    expect("secret123" not in error_message).to_be(True)
    expect("abc456" not in error_message).to_be(True)
    expect("other=keep" in error_message).to_be(True)


@test
async def ffmpeg_stderr_drain_timeout(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that stderr drain timeout is handled gracefully."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    never_finish: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

    call_count = 0

    async def _slow_stderr_readline() -> bytes:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return b"first error line\n"
        # Block forever on second call so the drain times out
        return await never_finish

    async def _stdout_read(_size: int = -1) -> bytes:
        await asyncio.sleep(0)
        return b""

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = _slow_stderr_readline
    mock_proc.returncode = 1

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch(f"{FFMPEG_PROXY}._STDERR_DRAIN_TIMEOUT", 0),
    ):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        await req.content.read()

    expect("FFmpeg conversion failed for device" in caplog.text).to_be(True)
    expect("first error line" in caplog.text).to_be(True)


@test
async def ffmpeg_proc_wait_timeout(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that proc.wait() timeout is handled gracefully."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    async def _stdout_read(_size: int = -1) -> bytes:
        await asyncio.sleep(0)
        return b""

    async def _proc_wait() -> None:
        # Block forever so wait_for times out
        await asyncio.Future()

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = AsyncMock(return_value=b"")
    mock_proc.returncode = None
    mock_proc.kill = MagicMock()
    mock_proc.wait = _proc_wait

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        patch(f"{FFMPEG_PROXY}._PROC_WAIT_TIMEOUT", 0),
        patch(f"{FFMPEG_PROXY}._STDERR_DRAIN_TIMEOUT", 0),
    ):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        await req.content.read()

    expect("Timed out waiting for ffmpeg process to exit" in caplog.text).to_be(True)


@test
async def ffmpeg_cleanup_on_cancellation(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test that ffmpeg process is killed when task is cancelled during cleanup."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    async def _stdout_read(_size: int = -1) -> bytes:
        await asyncio.sleep(0)
        return b""

    async def _proc_wait() -> None:
        # Simulate cancellation during proc.wait()
        raise asyncio.CancelledError

    mock_kill = MagicMock()
    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = AsyncMock(return_value=b"")
    mock_proc.returncode = None
    mock_proc.kill = mock_kill
    mock_proc.wait = _proc_wait

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        async with expect_raises_async(client_exceptions.ClientPayloadError):
            await req.content.read()

    # proc.kill should have been called (once in the initial check, once in the
    # CancelledError handler)
    expect(mock_kill.call_count >= 1).to_be(True)


@test
async def ffmpeg_unexpected_exception(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that unexpected exceptions during ffmpeg conversion are logged."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    async def _stdout_read_error(_size: int = -1) -> bytes:
        raise RuntimeError("unexpected read error")

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read_error
    mock_proc.stderr.readline = AsyncMock(return_value=b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        await req.content.read()

    expect("Unexpected error during ffmpeg conversion" in caplog.text).to_be(True)


@test
async def max_conversions_kills_running_process(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that exceeding max conversions kills a running ffmpeg process."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    stdout_futures: list[asyncio.Future[bytes]] = []
    mock_kills: list[MagicMock] = []
    procs_started = asyncio.Event()
    proc_count = 0

    def _make_mock_proc(*_args: object, **_kwargs: object) -> AsyncMock:
        """Create a mock ffmpeg process that blocks on stdout read."""
        nonlocal proc_count
        future: asyncio.Future[bytes] = hass.loop.create_future()
        stdout_futures.append(future)
        kill = MagicMock()
        mock_kills.append(kill)

        async def _stdout_read(_size: int = -1) -> bytes:
            return await future

        mock = AsyncMock()
        mock.stdout.read = _stdout_read
        mock.stderr.readline = AsyncMock(return_value=b"")
        mock.returncode = None
        mock.kill = kill
        proc_count += 1
        if proc_count >= 2:
            procs_started.set()
        return mock

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=_make_mock_proc,
    ):
        url1 = async_create_proxy_url(hass, device_id, "url1", media_format="mp3")
        url2 = async_create_proxy_url(hass, device_id, "url2", media_format="mp3")

        # Start both HTTP requests — each spawns an ffmpeg process that blocks
        task1 = hass.async_create_task(client.get(url1))
        task2 = hass.async_create_task(client.get(url2))

        # Wait until both ffmpeg processes have been created
        await procs_started.wait()
        expect(len(mock_kills)).to_equal(2)

        # Creating a third conversion should kill the oldest running process
        async_create_proxy_url(hass, device_id, "url3", media_format="mp3")
        expect("Stopping existing ffmpeg process" in caplog.text).to_be(True)
        mock_kills[0].assert_called_once()

        # Unblock stdout reads so background tasks can finish
        for future in stdout_futures:
            if not future.done():
                future.set_result(b"")

        await task1
        await task2


@test
async def lingering_process(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test that a new request stops the old ffmpeg process."""
    device_id = "1234"

    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".wav") as temp_file:
        _write_silence(temp_file.name, 1)
        wav_file = temp_file.name

        await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
        client = await hass_client()

        wav_url = pathname2url(wav_file)
        url1 = async_create_proxy_url(
            hass,
            device_id,
            wav_url,
            media_format="wav",
            rate=22050,
            channels=2,
            width=2,
        )

        # First request will start ffmpeg
        req1 = await client.get(url1)
        expect(req1.status).to_equal(HTTPStatus.OK)

        # Only read part of the data
        await req1.content.readexactly(100)

        # Allow another URL
        url2 = async_create_proxy_url(
            hass,
            device_id,
            wav_url,
            media_format="wav",
            rate=22050,
            channels=2,
            width=2,
        )

        req2 = await client.get(url2)
        expect(req2.status).to_equal(HTTPStatus.OK)

        wav_data = await req2.content.read()

        # All of the data should be there because this is a new ffmpeg process
        with (
            io.BytesIO(wav_data) as wav_io,
            wave.open(wav_io, "rb") as received_wav_file,
        ):
            # We can't use getnframes() here because the WAV header will be
            # incorrect. WAV encoders usually go back and update the WAV
            # header after all of the frames are written, but ffmpeg can't do
            # that because we're streaming the data. So instead, we just read
            # and count frames until we run out.
            num_frames = 0
            while chunk := received_wav_file.readframes(1024):
                num_frames += len(chunk) // (2 * 2)  # 2 channels, 16-bit samples

            expect(num_frames).to_equal(22050)  # 1s


@test
async def request_same_url_multiple_times(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test that the ffmpeg process is restarted if the same URL is requested multiple times."""
    device_id = "1234"

    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".wav") as temp_file:
        _write_silence(temp_file.name, 10)
        wav_file = temp_file.name

        await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
        client = await hass_client()

        wav_url = pathname2url(wav_file)
        url = async_create_proxy_url(
            hass,
            device_id,
            wav_url,
            media_format="wav",
            rate=22050,
            channels=2,
            width=2,
        )

        # First request will start ffmpeg
        req1 = await client.get(url)
        expect(req1.status).to_equal(HTTPStatus.OK)

        # Only read part of the data
        await req1.content.readexactly(100)

        # Second request should restart ffmpeg
        req2 = await client.get(url)
        expect(req2.status).to_equal(HTTPStatus.OK)

        wav_data = await req2.content.read()

        # All of the data should be there because this is a new ffmpeg process
        with (
            io.BytesIO(wav_data) as wav_io,
            wave.open(wav_io, "rb") as received_wav_file,
        ):
            num_frames = 0
            while chunk := received_wav_file.readframes(1024):
                num_frames += len(chunk) // (2 * 2)  # 2 channels, 16-bit samples

            expect(num_frames).to_equal(22050 * 10)  # 10s


@test
async def max_conversions_per_device(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test that each device has a maximum number of conversions (currently 2)."""
    max_conversions = 2
    device_ids = ["1234", "5678"]

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_paths = [
            os.path.join(temp_dir, f"{i}.wav") for i in range(max_conversions + 1)
        ]
        for wav_path in wav_paths:
            _write_silence(wav_path, 10)

        wav_urls = [pathname2url(p) for p in wav_paths]

        # Each device will have max + 1 conversions
        device_urls: dict[str, list[Any]] = {
            device_id: [
                async_create_proxy_url(
                    hass,
                    device_id,
                    wav_url,
                    media_format="wav",
                    rate=22050,
                    channels=2,
                    width=2,
                )
                for wav_url in wav_urls
            ]
            for device_id in device_ids
        }

        for urls in device_urls.values():
            # First URL should fail because it was overwritten by the others
            req = await client.get(urls[0])
            expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)

            # All other URLs should succeed
            for url in urls[1:]:
                req = await client.get(url)
                expect(req.status).to_equal(HTTPStatus.OK)


@test
async def abort_on_shutdown(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test we abort on Home Assistant shutdown."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".wav") as temp_file:
        with wave.open(temp_file.name, "wb") as wav_file:
            wav_file.setframerate(16000)
            wav_file.setsampwidth(2)
            wav_file.setnchannels(1)
            wav_file.writeframes(bytes(16000 * 2))  # 1s

        wav_url = pathname2url(temp_file.name)
        url = async_create_proxy_url(
            hass,
            device_id,
            wav_url,
            media_format="wav",
            rate=22050,
            channels=2,
            width=2,
        )

        # Get URL and start reading
        req = await client.get(url)
        expect(req.status).to_equal(HTTPStatus.OK)
        initial_mp3_data = await req.content.read(4)
        expect(initial_mp3_data).to_equal(b"RIFF")

        # Shut down Home Assistant
        await hass.async_stop()

        async with expect_raises_async(client_exceptions.ClientPayloadError):
            await req.content.read()
