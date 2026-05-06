"""The tests for the feedreader config flow."""

from unittest.mock import Mock, patch
import urllib

from tryke import Depends, expect, fixture, test

from homeassistant.components.feedreader.const import (
    CONF_MAX_ENTRIES,
    DEFAULT_MAX_ENTRIES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.feedreader import create_mock_entry
from tests.components.feedreader._fixtures import (
    feed_atom_htmlentities,
    feed_htmlentities,
    feed_one_event,
    feedparser,
    setup_entry,
)
from tests.components.feedreader.const import FEED_TITLE, URL, VALID_CONFIG_DEFAULT
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user(
    hass: HomeAssistant = Depends(hass_fixture),
    _feedparser: Mock = Depends(feedparser),
    _setup_entry: Mock = Depends(setup_entry),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: URL}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(FEED_TITLE)
    expect(result["data"][CONF_URL]).to_equal(URL)
    expect(result["options"][CONF_MAX_ENTRIES]).to_equal(DEFAULT_MAX_ENTRIES)


@test
async def user_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    feedparser: Mock = Depends(feedparser),
    _setup_entry: Mock = Depends(setup_entry),
    feed_one_event: bytes = Depends(feed_one_event),
) -> None:
    """Test starting a flow by user which results in an URL error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    feedparser.side_effect = urllib.error.URLError("Test")
    feedparser.return_value = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: URL}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "url_error"})

    feedparser.side_effect = None
    feedparser.return_value = feed_one_event
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: URL}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(FEED_TITLE)
    expect(result["data"][CONF_URL]).to_equal(URL)
    expect(result["options"][CONF_MAX_ENTRIES]).to_equal(DEFAULT_MAX_ENTRIES)


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _feedparser: Mock = Depends(feedparser),
) -> None:
    """Test starting a reconfigure flow."""
    entry = create_mock_entry(VALID_CONFIG_DEFAULT)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload"
    ) as mock_async_reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_URL: "http://other.rss.local/rss_feed.xml"},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_URL: "http://other.rss.local/rss_feed.xml"})

    await hass.async_block_till_done()
    expect(mock_async_reload.call_count).to_equal(1)


@test
async def reconfigure_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    feedparser: Mock = Depends(feedparser),
    _setup_entry: Mock = Depends(setup_entry),
    feed_one_event: bytes = Depends(feed_one_event),
) -> None:
    """Test reconfigure flow with URL error."""
    entry = create_mock_entry(VALID_CONFIG_DEFAULT)
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    feedparser.side_effect = urllib.error.URLError("Test")
    feedparser.return_value = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://other.rss.local/rss_feed.xml"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "url_error"})

    feedparser.side_effect = None
    feedparser.return_value = feed_one_event

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "http://other.rss.local/rss_feed.xml"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_URL: "http://other.rss.local/rss_feed.xml"})


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options flow."""
    entry = create_mock_entry(VALID_CONFIG_DEFAULT)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MAX_ENTRIES: 10},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_MAX_ENTRIES: 10})


@test.cases(
    test.case("htmlentities", fixture_name="feed_htmlentities", expected_title="RSS en español"),
    test.case("atom_htmlentities", fixture_name="feed_atom_htmlentities", expected_title="ATOM RSS en español"),
)
async def feed_htmlentities_flow(
    fixture_name: str,
    expected_title: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _feedparser: Mock = Depends(feedparser),
    _setup_entry: Mock = Depends(setup_entry),
    feed_htmlentities: bytes = Depends(feed_htmlentities),
    feed_atom_htmlentities: bytes = Depends(feed_atom_htmlentities),
) -> None:
    """Test starting a flow by user from a feed with HTML Entities in the title."""
    fixtures = {
        "feed_htmlentities": feed_htmlentities,
        "feed_atom_htmlentities": feed_atom_htmlentities,
    }
    with patch(
        "homeassistant.components.feedreader.config_flow.feedparser.http.get",
        side_effect=[fixtures[fixture_name]],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_URL: URL}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(expected_title)
