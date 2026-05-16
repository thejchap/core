"""The tests for the rest command platform."""

import base64
from http import HTTPStatus
from unittest.mock import patch

import aiohttp
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant.components.rest_command import DOMAIN
from homeassistant.const import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT_PLAIN,
    HTTP_DIGEST_AUTHENTICATION,
    SERVICE_RELOAD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import TEST_URL, ComponentSetup, setup_component as setup_component_fx

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async, mock_async_zeroconf
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def reload(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
) -> None:
    """Verify we can reload rest_command integration."""
    await setup_component()

    expect(hass.services.has_service(DOMAIN, "get_test")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "new_test")).to_be(False)

    new_config = {
        DOMAIN: {
            "new_test": {"url": "https://example.org", "method": "get"},
        }
    }
    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value=new_config,
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    expect(hass.services.has_service(DOMAIN, "new_test")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "get_test")).to_be(False)


@test
async def setup_tests(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
) -> None:
    """Set up test config and test it."""
    await setup_component()

    expect(hass.services.has_service(DOMAIN, "get_test")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "post_test")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "put_test")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "delete_test")).to_be(True)


@test
async def rest_command_timeout(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with timeout."""
    await setup_component()

    aioclient_mock.get(TEST_URL, exc=TimeoutError())

    async with expect_raises_async(
        HomeAssistantError,
        match=r'^Timeout when calling resource "https://example\.com/"$',
    ):
        await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def rest_command_aiohttp_error(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with aiohttp exception."""
    await setup_component()

    aioclient_mock.get(TEST_URL, exc=aiohttp.ClientError())

    async with expect_raises_async(
        HomeAssistantError,
        match=(
            r'^Client error occurred when calling resource "https://example\.com/"$'
        ),
    ):
        await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def rest_command_http_error(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with status code 400."""
    await setup_component()

    aioclient_mock.get(TEST_URL, status=HTTPStatus.BAD_REQUEST)

    await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def rest_command_auth(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with auth credential."""
    await setup_component()

    aioclient_mock.get(TEST_URL, content=b"success")

    await hass.services.async_call(DOMAIN, "auth_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def rest_command_digest_auth(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with HTTP digest authentication."""
    config = {
        "digest_auth_test": {
            "url": TEST_URL,
            "method": "get",
            "username": "test_user",
            "password": "test_pass",
            "authentication": HTTP_DIGEST_AUTHENTICATION,
        }
    }

    await setup_component(config)

    with patch("aiohttp.ClientSession.get") as mock_get:

        async def async_iter_chunks(self, chunk_size):
            yield b"success"

        mock_response = type(
            "MockResponse",
            (),
            {
                "status": 200,
                "content_type": "text/plain",
                "headers": {},
                "url": TEST_URL,
                "content": type(
                    "MockContent", (), {"iter_chunked": async_iter_chunks}
                )(),
            },
        )()
        mock_get.return_value.__aenter__.return_value = mock_response

        await hass.services.async_call(DOMAIN, "digest_auth_test", {}, blocking=True)

        expect(mock_get.called).to_be(True)
        call_kwargs = mock_get.call_args[1]
        expect("middlewares" in call_kwargs).to_be(True)
        expect(len(call_kwargs["middlewares"])).to_equal(1)
        expect(
            isinstance(call_kwargs["middlewares"][0], aiohttp.DigestAuthMiddleware)
        ).to_be(True)


@test
async def rest_command_form_data(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with post form data."""
    await setup_component()

    aioclient_mock.post(TEST_URL, content=b"success")

    await hass.services.async_call(DOMAIN, "post_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(aioclient_mock.mock_calls[0][2]).to_equal(b"test")


@test.cases(
    test.case("get", method="get"),
    test.case("patch", method="patch"),
    test.case("post", method="post"),
    test.case("put", method="put"),
    test.case("delete", method="delete"),
)
async def rest_command_methods(
    method: str,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test various http methods."""
    await setup_component()

    aioclient_mock.request(method=method, url=TEST_URL, content=b"success")

    await hass.services.async_call(DOMAIN, f"{method}_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def rest_command_headers(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Call a rest command with custom headers and content types."""
    header_config_variations = {
        "no_headers_test": {},
        "content_type_test": {"content_type": CONTENT_TYPE_TEXT_PLAIN},
        "headers_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                "User-Agent": "Mozilla/5.0",
            }
        },
        "headers_and_content_type_test": {
            "headers": {"Accept": CONTENT_TYPE_JSON},
            "content_type": CONTENT_TYPE_TEXT_PLAIN,
        },
        "headers_and_content_type_override_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                aiohttp.hdrs.CONTENT_TYPE: "application/pdf",
            },
            "content_type": CONTENT_TYPE_TEXT_PLAIN,
        },
        "headers_template_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                "User-Agent": "Mozilla/{{ 3 + 2 }}.0",
            }
        },
        "headers_and_content_type_override_template_test": {
            "headers": {
                "Accept": "application/{{ 1 + 1 }}json",
                aiohttp.hdrs.CONTENT_TYPE: "application/pdf",
            },
            "content_type": "text/json",
        },
    }

    for variation in header_config_variations.values():
        variation.update({"url": TEST_URL, "method": "post", "payload": "test data"})

    await setup_component(header_config_variations)

    aioclient_mock.post(TEST_URL, content=b"success")

    for test_service in (
        "no_headers_test",
        "content_type_test",
        "headers_test",
        "headers_and_content_type_test",
        "headers_and_content_type_override_test",
        "headers_template_test",
        "headers_and_content_type_override_template_test",
    ):
        await hass.services.async_call(DOMAIN, test_service, {}, blocking=True)

    await hass.async_block_till_done()
    expect(len(aioclient_mock.mock_calls)).to_equal(7)

    expect(aioclient_mock.mock_calls[0][3] is None).to_be(True)

    expect(len(aioclient_mock.mock_calls[1][3])).to_equal(1)
    expect(aioclient_mock.mock_calls[1][3].get(aiohttp.hdrs.CONTENT_TYPE)).to_equal(
        CONTENT_TYPE_TEXT_PLAIN
    )

    expect(len(aioclient_mock.mock_calls[2][3])).to_equal(2)
    expect(aioclient_mock.mock_calls[2][3].get("Accept")).to_equal(CONTENT_TYPE_JSON)
    expect(aioclient_mock.mock_calls[2][3].get("User-Agent")).to_equal("Mozilla/5.0")

    expect(len(aioclient_mock.mock_calls[3][3])).to_equal(2)
    expect(aioclient_mock.mock_calls[3][3].get(aiohttp.hdrs.CONTENT_TYPE)).to_equal(
        CONTENT_TYPE_TEXT_PLAIN
    )
    expect(aioclient_mock.mock_calls[3][3].get("Accept")).to_equal(CONTENT_TYPE_JSON)

    expect(len(aioclient_mock.mock_calls[4][3])).to_equal(2)
    expect(aioclient_mock.mock_calls[4][3].get(aiohttp.hdrs.CONTENT_TYPE)).to_equal(
        CONTENT_TYPE_TEXT_PLAIN
    )
    expect(aioclient_mock.mock_calls[4][3].get("Accept")).to_equal(CONTENT_TYPE_JSON)

    expect(len(aioclient_mock.mock_calls[5][3])).to_equal(2)
    expect(aioclient_mock.mock_calls[5][3].get("Accept")).to_equal(CONTENT_TYPE_JSON)
    expect(aioclient_mock.mock_calls[5][3].get("User-Agent")).to_equal("Mozilla/5.0")

    expect(len(aioclient_mock.mock_calls[6][3])).to_equal(2)
    expect(aioclient_mock.mock_calls[6][3].get(aiohttp.hdrs.CONTENT_TYPE)).to_equal(
        "text/json"
    )
    expect(aioclient_mock.mock_calls[6][3].get("Accept")).to_equal("application/2json")


@test
async def rest_command_get_response_plaintext(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Get rest_command response, text."""
    await setup_component()

    aioclient_mock.get(
        TEST_URL, content=b"success", headers={"content-type": "text/plain"}
    )

    response = await hass.services.async_call(
        DOMAIN, "get_test", {}, blocking=True, return_response=True
    )

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(response["content"]).to_equal("success")
    expect(response["status"]).to_equal(200)
    expect(response["headers"]).to_equal({"content-type": "text/plain"})


@test
async def rest_command_get_response_json(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Get rest_command response, json."""
    await setup_component()

    aioclient_mock.get(
        TEST_URL,
        json={"status": "success", "number": 42},
        headers={"content-type": "application/json"},
    )

    response = await hass.services.async_call(
        DOMAIN, "get_test", {}, blocking=True, return_response=True
    )

    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(response["content"]["status"]).to_equal("success")
    expect(response["content"]["number"]).to_equal(42)
    expect(response["status"]).to_equal(200)
    expect(response["headers"]).to_equal({"content-type": "application/json"})


@test
async def rest_command_get_response_malformed_json(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Get rest_command response, malformed json."""
    await setup_component()

    aioclient_mock.get(
        TEST_URL,
        content=b'{"status": "failure", 42',
        headers={"content-type": "application/json"},
    )

    response = await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)
    expect(bool(response)).to_be(False)

    raised_json: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            DOMAIN, "get_test", {}, blocking=True, return_response=True
        )
    except HomeAssistantError as err:
        raised_json = err
    expect(raised_json is not None).to_be(True)
    expect(str(raised_json)).to_equal(
        'The response of "https://example.com/" could not be decoded as JSON'
    )


@test
async def rest_command_get_response_none(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Get rest_command response, other."""
    await setup_component()

    png = base64.decodebytes(
        b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQ"
        b"UAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAAPSURBVBhXY/h/ku////8AECAE1JZPvDAAAAAASUVORK5CYII="
    )

    aioclient_mock.get(
        TEST_URL,
        content=png,
        headers={"content-type": "text/plain"},
    )

    response = await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)
    expect(bool(response)).to_be(False)

    async with expect_raises_async(
        HomeAssistantError,
        match=(
            r'^The response of "https://example\.com/" could not be decoded as text$'
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN, "get_test", {}, blocking=True, return_response=True
        )

    expect(bool(response)).to_be(False)


@test
async def rest_command_response_iter_chunked(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Ensure response is consumed when return_response is False."""
    await setup_component()

    png = base64.decodebytes(
        b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7QOjdAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQ"
        b"UAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAAPSURBVBhXY/h/ku////8AECAE1JZPvDAAAAAASUVORK5CYII="
    )
    aioclient_mock.get(TEST_URL, content=png)

    with patch("aiohttp.StreamReader.iter_chunked", autospec=True) as mock_iter_chunked:
        response = await hass.services.async_call(DOMAIN, "get_test", {}, blocking=True)

        expect(response is None).to_be(True)

        expect(mock_iter_chunked.called).to_be(True)


@test
async def rest_command_skip_url_encoding(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Check URL encoding."""
    config = {
        "skip_url_encoding_test": {
            "url": "0%2C",
            "method": "get",
            "skip_url_encoding": True,
        },
        "with_url_encoding_test": {
            "url": "1,",
            "method": "get",
        },
    }

    await setup_component(config)

    aioclient_mock.get(URL("0%2C", encoded=True), content=b"success")
    aioclient_mock.get(URL("1,"), content=b"success")

    await hass.services.async_call(DOMAIN, "skip_url_encoding_test", {}, blocking=True)
    await hass.services.async_call(DOMAIN, "with_url_encoding_test", {}, blocking=True)

    expect(len(aioclient_mock.mock_calls)).to_equal(2)
    expect(str(aioclient_mock.mock_calls[0][1])).to_equal("0%2C")
    expect(str(aioclient_mock.mock_calls[1][1])).to_equal("1,")
