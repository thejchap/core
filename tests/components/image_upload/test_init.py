"""Test that we can upload images."""

import pathlib
import tempfile
from unittest.mock import patch

from aiohttp import ClientSession, ClientWebSocketResponse
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import TEST_IMAGE

from tests.hass_fixtures import (
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@fixture
def _trigger_executor(_hass: HomeAssistant = Depends(hass_fixture)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def upload_image(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test we can upload an image."""
    now = dt_util.utcnow()
    freezer.move_to(now)

    with (
        tempfile.TemporaryDirectory() as tempdir,
        patch.object(hass.config, "path", return_value=tempdir),
    ):
        expect(await async_setup_component(hass, "image_upload", {})).to_be_truthy()
        ws_client: ClientWebSocketResponse = await hass_ws_client()
        client: ClientSession = await hass_client()

        with TEST_IMAGE.open("rb") as fp:
            res = await client.post("/api/image/upload", data={"file": fp})

        expect(res.status).to_equal(200)

        item = await res.json()

        expect(item["content_type"]).to_equal("image/png")
        expect(item["filesize"]).to_equal(38847)
        expect(item["name"]).to_equal("logo.png")
        expect(item["uploaded_at"]).to_equal(now.isoformat())

        tempdir = pathlib.Path(tempdir)
        item_folder: pathlib.Path = tempdir / item["id"]
        test_image_bytes = TEST_IMAGE.read_bytes()
        expect((item_folder / "original").read_bytes()).to_equal(test_image_bytes)

        # fetch original image
        res = await client.get(f"/api/image/serve/{item['id']}/original")
        expect(res.status).to_equal(200)
        fetched_image_bytes = await res.read()
        expect(fetched_image_bytes).to_equal(test_image_bytes)

        # fetch non-existing image
        res = await client.get("/api/image/serve/non-existing/256x256")
        expect(res.status).to_equal(404)

        # fetch invalid sizes
        for inv_size in ("256", "256x25A", "100x100", "25Ax256"):
            res = await client.get(f"/api/image/serve/{item['id']}/{inv_size}")
            expect(res.status).to_equal(400)

        # fetch resized version
        res = await client.get(f"/api/image/serve/{item['id']}/256x256")
        expect(res.status).to_equal(200)
        expect((item_folder / "256x256").is_file()).to_be_truthy()

        # List item
        await ws_client.send_json({"id": 6, "type": "image/list"})
        msg = await ws_client.receive_json()

        expect(msg["id"]).to_equal(6)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        expect(msg["result"]).to_equal([item])

        # Delete item
        await ws_client.send_json(
            {"id": 7, "type": "image/delete", "image_id": item["id"]}
        )
        msg = await ws_client.receive_json()

        expect(msg["id"]).to_equal(7)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()

        # Ensure removed from disk
        expect(item_folder.is_dir()).to_be_falsy()
