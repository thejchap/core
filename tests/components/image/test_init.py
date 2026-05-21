"""The tests for the image component."""

from datetime import datetime
from http import HTTPStatus
import ssl
from unittest.mock import MagicMock, mock_open, patch

from aiohttp import hdrs
from freezegun.api import FrozenDateTimeFactory
import httpx
from tryke import Depends, expect, fixture, test

from homeassistant.components import image
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component

from ._fixtures import (
    MockImageEntity,
    MockImageEntityCapitalContentType,
    MockImageEntityInvalidContentType,
    MockImageNoDataEntity,
    MockImageNoStateEntity,
    MockImagePlatform,
    MockImageSyncEntity,
    MockURLImageEntity,
    mock_image_config_entry as mock_image_config_entry_fixture,
    mock_image_platform as mock_image_platform_fixture,
)

from tests.common import (
    MockModule,
    async_fire_time_changed,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    hass_client_no_auth as hass_client_no_auth_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async, respx_mock_session
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@fixture
def freeze_2023_04_01(
    _trigger: int = Depends(_trigger_executor),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> FrozenDateTimeFactory:
    """Freeze time at 2023-04-01."""
    freezer.move_to("2023-04-01 00:00:00+00:00")
    return freezer


@test
async def state(
    _freeze: FrozenDateTimeFactory = Depends(freeze_2023_04_01),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    _platform: None = Depends(mock_image_platform_fixture),
) -> None:
    """Test image state."""
    state = hass.states.get("image.test")
    expect(state.state).to_equal("2023-04-01T00:00:00+00:00")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
            "friendly_name": "Test",
        }
    )


@test
async def config_entry(
    _freeze: FrozenDateTimeFactory = Depends(freeze_2023_04_01),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    _config_entry: ConfigEntry = Depends(mock_image_config_entry_fixture),
) -> None:
    """Test setting up an image platform from a config entry."""
    state = hass.states.get("image.test")
    expect(state.state).to_equal("2023-04-01T00:00:00+00:00")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
            "friendly_name": "Test",
        }
    )


@test
async def state_attr(
    _freeze: FrozenDateTimeFactory = Depends(freeze_2023_04_01),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test image state with entity picture from attr."""
    mock_integration(hass, MockModule(domain="test"))
    entity = MockImageEntity(hass)
    entity._attr_entity_picture = "abcd"
    mock_platform(hass, "test.image", MockImagePlatform([entity]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("image.test")
    expect(state.state).to_equal("2023-04-01T00:00:00+00:00")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": "abcd",
            "friendly_name": "Test",
        }
    )


@test
async def no_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test image state."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageNoStateEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("image.test")
    expect(state.state).to_equal("unknown")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
            "friendly_name": "Test",
        }
    )


@test
async def no_valid_content_type(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test invalid content type."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(
        hass, "test.image", MockImagePlatform([MockImageEntityInvalidContentType(hass)])
    )
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    client = await hass_client()

    state = hass.states.get("image.test")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
            "friendly_name": "Test",
        }
    )
    resp = await client.get(f"/api/image_proxy/image.test?token={access_token}")
    expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)


@test
async def valid_but_capitalized_content_type(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test invalid content type."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(
        hass, "test.image", MockImagePlatform([MockImageEntityCapitalContentType(hass)])
    )
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    client = await hass_client()

    state = hass.states.get("image.test")
    access_token = state.attributes["access_token"]
    expect(state.attributes).to_equal(
        {
            "access_token": access_token,
            "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
            "friendly_name": "Test",
        }
    )
    resp = await client.get(f"/api/image_proxy/image.test?token={access_token}")
    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def fetch_image_authenticated(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    _platform: None = Depends(mock_image_platform_fixture),
) -> None:
    """Test fetching an image with an authenticated client."""
    client = await hass_client()

    # Using HEAD
    resp = await client.head("/api/image_proxy/image.test")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.content_type).to_equal("image/jpeg")
    expect(resp.content_length).to_equal(4)

    resp = await client.head("/api/image_proxy/image.unknown")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)

    # Using GET
    resp = await client.get("/api/image_proxy/image.test")
    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.read()
    expect(body).to_equal(b"Test")
    expect(resp.content_type).to_equal("image/jpeg")
    expect(resp.content_length).to_equal(4)

    resp = await client.get("/api/image_proxy/image.unknown")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def fetch_image_fail(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    _platform: None = Depends(mock_image_platform_fixture),
) -> None:
    """Test fetching an image with an authenticated client."""
    client = await hass_client()

    with patch.object(MockImageEntity, "async_image", side_effect=TimeoutError):
        resp = await client.get("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)


@test
async def fetch_image_sync(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test fetching an image with an authenticated client."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageSyncEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    client = await hass_client()

    resp = await client.get("/api/image_proxy/image.test")
    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.read()
    expect(body).to_equal(b"Test")


@test
async def fetch_image_unauthenticated(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    _platform: None = Depends(mock_image_platform_fixture),
) -> None:
    """Test fetching an image with an unauthenticated client."""
    client = await hass_client_no_auth()

    resp = await client.get("/api/image_proxy/image.test")
    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)

    resp = await client.get("/api/image_proxy/image.test")
    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)

    resp = await client.get(
        "/api/image_proxy/image.test", headers={hdrs.AUTHORIZATION: "blabla"}
    )
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    state = hass.states.get("image.test")
    resp = await client.get(state.attributes["entity_picture"])
    expect(resp.status).to_equal(HTTPStatus.OK)
    body = await resp.read()
    expect(body).to_equal(b"Test")

    resp = await client.get("/api/image_proxy/image.unknown")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def fetch_image_url_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test fetching an image with an authenticated client."""
    async with respx_mock_session() as respx_mock:
        respx_mock.get("https://example.com/myimage.jpg").respond(
            status_code=HTTPStatus.OK, content_type="image/png", content=b"Test"
        )

        mock_integration(hass, MockModule(domain="test"))
        mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
        expect(
            await async_setup_component(
                hass, image.DOMAIN, {"image": {"platform": "test"}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

        client = await hass_client()

        # Using HEAD
        resp = await client.head("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.OK)
        expect(resp.content_type).to_equal("image/png")
        expect(resp.content_length).to_equal(4)

        # Using GET
        resp = await client.get("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.OK)
        body = await resp.read()
        expect(body).to_equal(b"Test")
        expect(resp.content_type).to_equal("image/png")
        expect(resp.content_length).to_equal(4)


@test.cases(
    test.case("request_error", side_effect=httpx.RequestError("server offline", request=MagicMock())),
    test.case("timeout", side_effect=httpx.TimeoutException),
    test.case("ssl_error", side_effect=ssl.SSLError),
)
async def fetch_image_url_exception(
    side_effect: Exception,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test fetching an image with an authenticated client."""
    async with respx_mock_session() as respx_mock:
        respx_mock.get("https://example.com/myimage.jpg").mock(side_effect=side_effect)

        mock_integration(hass, MockModule(domain="test"))
        mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
        expect(
            await async_setup_component(
                hass, image.DOMAIN, {"image": {"platform": "test"}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

        client = await hass_client()

        resp = await client.get("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)


@test.cases(
    test.case("none", content_type=None),
    test.case("text_plain", content_type="text/plain"),
)
async def fetch_image_url_wrong_content_type(
    content_type: str | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test fetching an image with an authenticated client."""
    async with respx_mock_session() as respx_mock:
        respx_mock.get("https://example.com/myimage.jpg").respond(
            status_code=HTTPStatus.OK, content_type=content_type, content=b"Test"
        )

        mock_integration(hass, MockModule(domain="test"))
        mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
        expect(
            await async_setup_component(
                hass, image.DOMAIN, {"image": {"platform": "test"}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

        client = await hass_client()

        resp = await client.get("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)


@test.cases(
    test.case("png", content=b"\x89PNG", content_type="image/png"),
    test.case("jpeg_db", content=b"\xff\xd8\xff\xdb", content_type="image/jpeg"),
    test.case("jpeg_e0", content=b"\xff\xd8\xff\xe0", content_type="image/jpeg"),
    test.case("jpeg_ed", content=b"\xff\xd8\xff\xed", content_type="image/jpeg"),
    test.case("jpeg_ee", content=b"\xff\xd8\xff\xee", content_type="image/jpeg"),
    test.case("jpeg_e1", content=b"\xff\xd8\xff\xe1", content_type="image/jpeg"),
    test.case("jpeg_e2", content=b"\xff\xd8\xff\xe2", content_type="image/jpeg"),
    test.case("gif89a", content=b"GIF89a", content_type="image/gif"),
    test.case("gif87a", content=b"GIF87a", content_type="image/gif"),
    test.case("webp", content=b"RIFF", content_type="image/webp"),
    test.case("tiff_ii", content=b"\x49\x49\x2a\x00", content_type="image/tiff"),
    test.case("tiff_mm", content=b"\x4d\x4d\x00\x2a", content_type="image/tiff"),
)
async def fetch_image_url_infer_content_type_from_magic_number(
    content: bytes,
    content_type: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test fetching an image and inferring content-type from magic number."""
    async with respx_mock_session() as respx_mock:
        respx_mock.get("https://example.com/myimage.jpg").respond(
            status_code=HTTPStatus.OK, content=content
        )

        mock_integration(hass, MockModule(domain="test"))
        mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
        expect(
            await async_setup_component(
                hass, image.DOMAIN, {"image": {"platform": "test"}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

        client = await hass_client()

        resp = await client.get("/api/image_proxy/image.test")
        expect(resp.status).to_equal(HTTPStatus.OK)
        body = await resp.read()
        expect(body).to_equal(content)
        expect(resp.content_type).to_equal(content_type)


@test
async def image_stream(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test image stream."""
    mock_integration(hass, MockModule(domain="test"))
    mock_image = MockURLImageEntity(hass)
    mock_platform(hass, "test.image", MockImagePlatform([mock_image]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    client = await hass_client()

    close_future = hass.loop.create_future()
    original_get_still_stream = image.async_get_still_stream

    async def _wrap_async_get_still_stream(*args, **kwargs):
        result = await original_get_still_stream(*args, **kwargs)
        hass.loop.call_soon(close_future.set_result, None)
        return result

    with patch(
        "homeassistant.components.image.async_get_still_stream",
        _wrap_async_get_still_stream,
    ):
        with patch.object(mock_image, "async_image", return_value=b""):
            resp = await client.get("/api/image_proxy_stream/image.test")
            expect(resp.closed).to_be_falsy()
            expect(resp.status).to_equal(HTTPStatus.OK)

            mock_image.image_last_updated = datetime.now()
            mock_image.async_write_ha_state()
            # Two blocks to ensure the frame is written
            await hass.async_block_till_done()
            await hass.async_block_till_done()

        with patch.object(mock_image, "async_image", return_value=b"") as mock:
            # Simulate a "keep alive" frame
            freezer.tick(55)
            async_fire_time_changed(hass)
            # Two blocks to ensure the frame is written
            await hass.async_block_till_done()
            await hass.async_block_till_done()
            mock.assert_called_once()

        with patch.object(mock_image, "async_image", return_value=None):
            freezer.tick(55)
            async_fire_time_changed(hass)
            # Two blocks to ensure the frame is written
            await hass.async_block_till_done()
            await hass.async_block_till_done()

    await close_future


@test
async def get_image_action(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platform: None = Depends(mock_image_platform_fixture),
) -> None:
    """Test get_image action."""
    image_data = await image.async_get_image(hass, "image.test")
    expect(image_data).to_equal(image.Image(content_type="image/jpeg", content=b"Test"))

    async with expect_raises_async(HomeAssistantError, match="not found"):
        await image.async_get_image(hass, "image.unknown")


@test
async def snapshot_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test snapshot service."""
    mopen = mock_open()
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageSyncEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    with (
        patch("homeassistant.components.image.open", mopen, create=True),
        patch("homeassistant.components.image.os.makedirs"),
        patch.object(hass.config, "is_allowed_path", return_value=True),
    ):
        await hass.services.async_call(
            image.DOMAIN,
            image.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: "image.test",
                image.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )

        mock_write = mopen().write

        expect(len(mock_write.mock_calls)).to_equal(1)
        expect(mock_write.mock_calls[0][1][0]).to_equal(b"Test")


@test
async def snapshot_service_no_image(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test snapshot service with no image."""
    mopen = mock_open()
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageNoDataEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    with (
        patch("homeassistant.components.image.open", mopen, create=True),
        patch("homeassistant.components.image.os.makedirs"),
        patch.object(hass.config, "is_allowed_path", return_value=True),
    ):
        await hass.services.async_call(
            image.DOMAIN,
            image.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: "image.test",
                image.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )

        mock_write = mopen().write

        expect(len(mock_write.mock_calls)).to_equal(0)


@test
async def snapshot_service_not_allowed_path(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test snapshot service with a not allowed path."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockURLImageEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    async with expect_raises_async(HomeAssistantError, match="/test/snapshot.jpg"):
        await hass.services.async_call(
            image.DOMAIN,
            image.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: "image.test",
                image.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )


@test
async def snapshot_service_os_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test snapshot service with os error."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageSyncEntity(hass)]))
    expect(
        await async_setup_component(hass, image.DOMAIN, {"image": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.makedirs", side_effect=OSError),
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                image.DOMAIN,
                image.SERVICE_SNAPSHOT,
                {
                    ATTR_ENTITY_ID: "image.test",
                    image.ATTR_FILENAME: "/test/snapshot.jpg",
                },
                blocking=True,
            )
