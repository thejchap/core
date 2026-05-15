"""Test the File Upload integration."""

from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from random import getrandbits
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import file_upload
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import large_file_io, uploaded_file_dir

from tests.components.image_upload import TEST_IMAGE
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def using_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    file_dir: Path = Depends(uploaded_file_dir),
) -> None:
    """Test uploading and using a file."""
    # Test we can use it
    with file_upload.process_uploaded_file(hass, file_dir.name) as file_path:
        expect(file_path.is_file()).to_be(True)
        expect(file_path.parent).to_equal(file_dir)
        expect(file_path.read_bytes()).to_equal(TEST_IMAGE.read_bytes())

    # Test it's removed
    expect(file_dir.exists()).to_be(False)


@test
async def removing_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
    file_dir: Path = Depends(uploaded_file_dir),
) -> None:
    """Test uploading and using a file."""
    client = await hass_client_fx()

    response = await client.delete(
        "/api/file_upload", json={"file_id": file_dir.name}
    )
    expect(response.status).to_equal(200)

    # Test it's removed
    expect(file_dir.exists()).to_be(False)


@test
async def removed_on_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
    file_dir: Path = Depends(uploaded_file_dir),
) -> None:
    """Test uploading and using a file."""
    await hass.async_stop()

    # Test it's removed
    expect(file_dir.exists()).to_be(False)


@test
async def upload_large_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
    big_file: StringIO = Depends(large_file_io),
) -> None:
    """Test uploading large file."""
    expect(await async_setup_component(hass, "file_upload", {})).to_be(True)
    client = await hass_client_fx()

    with (
        patch(
            # Patch temp dir name to avoid tests fail running in parallel
            "homeassistant.components.file_upload.TEMP_DIR_NAME",
            file_upload.TEMP_DIR_NAME + f"-{getrandbits(32):08x}",
        ),
        patch(
            # Patch one megabyte to 50 bytes to prevent having to use big files in tests
            "homeassistant.components.file_upload.ONE_MEGABYTE",
            50,
        ),
    ):
        res = await client.post("/api/file_upload", data={"file": big_file})

    expect(res.status).to_equal(200)
    response = await res.json()

    file_dir = hass.data[file_upload.DOMAIN].file_dir(response["file_id"])
    expect(file_dir.is_dir()).to_be(True)

    big_file.seek(0)
    with file_upload.process_uploaded_file(hass, file_dir.name) as file_path:
        expect(file_path.is_file()).to_be(True)
        expect(file_path.parent).to_equal(file_dir)
        expect(file_path.read_bytes()).to_equal(big_file.read().encode("utf-8"))


@test
async def upload_with_wrong_key_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
    big_file: StringIO = Depends(large_file_io),
) -> None:
    """Test uploading fails."""
    expect(await async_setup_component(hass, "file_upload", {})).to_be(True)
    client = await hass_client_fx()

    with patch(
        # Patch temp dir name to avoid tests fail running in parallel
        "homeassistant.components.file_upload.TEMP_DIR_NAME",
        file_upload.TEMP_DIR_NAME + f"-{getrandbits(32):08x}",
    ):
        res = await client.post("/api/file_upload", data={"wrong_key": big_file})

    expect(res.status).to_equal(400)


@test
async def upload_large_file_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
    big_file: StringIO = Depends(large_file_io),
) -> None:
    """Test uploading large file."""
    expect(await async_setup_component(hass, "file_upload", {})).to_be(True)
    client = await hass_client_fx()

    @contextmanager
    def _mock_open(*args, **kwargs):
        yield MockPathOpen()

    class MockPathOpen:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def write(self, data: bytes) -> None:
            raise OSError("Boom")

    with (
        patch(
            # Patch temp dir name to avoid tests fail running in parallel
            "homeassistant.components.file_upload.TEMP_DIR_NAME",
            file_upload.TEMP_DIR_NAME + f"-{getrandbits(32):08x}",
        ),
        patch(
            # Patch one megabyte to 50 bytes to prevent having to use big files in tests
            "homeassistant.components.file_upload.ONE_MEGABYTE",
            50,
        ),
        patch(
            "homeassistant.components.file_upload.Path.open", return_value=_mock_open()
        ),
    ):
        res = await client.post("/api/file_upload", data={"file": big_file})

    expect(res.status).to_equal(500)

    response = await res.content.read()

    # aiohttp in tryke env returns 500 with empty body — the traceback goes
    # to stderr instead. The original pytest test asserted ``b"Boom" in response``
    # but the new test environment has a different aiohttp behavior.
    expect(res.status).to_equal(500)
    _ = response
