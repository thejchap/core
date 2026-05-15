"""Tryke fixtures for file_upload tests."""

from io import StringIO
from pathlib import Path
from random import getrandbits
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components import file_upload
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.components.image_upload import TEST_IMAGE
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client,
)


@fixture
def large_file_io() -> StringIO:
    """Generate a file on the fly. Simulates a large file."""
    return StringIO(
        2
        * "Home Assistant is awesome. Open source home automation that puts local control and privacy first."
    )


@fixture
async def uploaded_file_dir(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_fx: ClientSessionGenerator = Depends(hass_client),
) -> Path:
    """Test uploading and using a file."""
    await async_setup_component(hass, "file_upload", {})
    client = await hass_client_fx()

    with (
        patch(
            # Patch temp dir name to avoid tests fail running in parallel
            "homeassistant.components.file_upload.TEMP_DIR_NAME",
            file_upload.TEMP_DIR_NAME + f"-{getrandbits(32):08x}",
        ),
        TEST_IMAGE.open("rb") as fp,
    ):
        res = await client.post("/api/file_upload", data={"file": fp})

    assert res.status == 200
    response = await res.json()

    file_dir = hass.data[file_upload.DOMAIN].file_dir(response["file_id"])
    assert file_dir.is_dir()
    return file_dir
