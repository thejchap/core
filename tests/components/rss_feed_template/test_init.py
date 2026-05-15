"""The tests for the rss_feed_api component."""

from http import HTTPStatus

from aiohttp.test_utils import TestClient
from defusedxml import ElementTree
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
async def mock_http_client(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> TestClient:
    """Set up test fixture."""
    config = {
        "rss_feed_template": {
            "testfeed": {
                "title": "feed title is {{states.test.test1.state}}",
                "items": [
                    {
                        "title": "item title is {{states.test.test2.state}}",
                        "description": "desc {{states.test.test3.state}}",
                    }
                ],
            }
        }
    }

    await async_setup_component(hass, "rss_feed_template", config)
    return await hass_client()


@test
async def get_nonexistant_feed(
    mock_http_client: TestClient = Depends(mock_http_client),
) -> None:
    """Test if we can retrieve the correct rss feed."""
    resp = await mock_http_client.get("/api/rss_template/otherfeed")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def get_rss_feed(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client),
) -> None:
    """Test if we can retrieve the correct rss feed."""
    hass.states.async_set("test.test1", "a_state_1")
    hass.states.async_set("test.test2", "a_state_2")
    hass.states.async_set("test.test3", "a_state_3")

    resp = await mock_http_client.get("/api/rss_template/testfeed")
    expect(resp.status).to_equal(HTTPStatus.OK)

    text = await resp.text()

    xml = ElementTree.fromstring(text)
    feed_title = xml.find("./channel/title").text
    item_title = xml.find("./channel/item/title").text
    item_description = xml.find("./channel/item/description").text
    expect(feed_title).to_equal("feed title is a_state_1")
    expect(item_title).to_equal("item title is a_state_2")
    expect(item_description).to_equal("desc a_state_3")
