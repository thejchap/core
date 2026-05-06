"""Test the Holiday config flow."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from freezegun import freeze_time
from holidays import UNOFFICIAL
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.holiday.const import (
    CONF_CATEGORIES,
    CONF_PROVINCE,
    DOMAIN,
)
from homeassistant.const import CONF_COUNTRY, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry
from tests.components.holiday._fixtures import mock_setup_entry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "DE"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_PROVINCE: "BW"},
    )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Germany, BW")
    expect(result3["data"]).to_equal({"country": "DE", "province": "BW"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_no_subdivision(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the forms correctly without subdivision."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "AL"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Albania")
    expect(result2["data"]).to_equal({"country": "AL"})


@test
async def form_translated_title(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the title gets translated."""
    hass.config.language = "de"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "AL"},
    )
    await hass.async_block_till_done()

    expect(result2["title"]).to_equal("Albanien")


@test
async def single_combination_country_province(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that configuring more than one instance is rejected."""
    data_de = {CONF_COUNTRY: "DE", CONF_PROVINCE: "BW"}
    data_al = {CONF_COUNTRY: "AL"}
    MockConfigEntry(domain=DOMAIN, data=data_de).add_to_hass(hass)
    MockConfigEntry(domain=DOMAIN, data=data_al).add_to_hass(hass)

    result_al = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=data_al,
    )
    expect(result_al["type"]).to_be(FlowResultType.ABORT)
    expect(result_al["reason"]).to_equal("already_configured")

    result_de_step1 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=data_de,
    )
    expect(result_de_step1["type"]).to_be(FlowResultType.FORM)

    result_de_step2 = await hass.config_entries.flow.async_configure(
        result_de_step1["flow_id"],
        {CONF_PROVINCE: data_de[CONF_PROVINCE]},
    )
    expect(result_de_step2["type"]).to_be(FlowResultType.ABORT)
    expect(result_de_step2["reason"]).to_equal("already_configured")


@test
async def form_babel_unresolved_language(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the config flow if using not babel supported language."""
    hass.config.language = "en-XX"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "AL"},
    )
    await hass.async_block_till_done()

    expect(result["title"]).to_equal("Albania")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "DE"},
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "BW"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Germany, BW")
    expect(result["data"]).to_equal({"country": "DE", "province": "BW"})


@test
async def form_babel_replace_dash_with_underscore(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the config flow if using language with dash."""
    hass.config.language = "en-GB"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "AL"},
    )
    await hass.async_block_till_done()

    expect(result["title"]).to_equal("Albania")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_COUNTRY: "DE"},
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "BW"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Germany, BW")
    expect(result["data"]).to_equal({"country": "DE", "province": "BW"})


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Germany, BW",
        data={"country": "DE", "province": "BW"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "NW"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.title).to_equal("Germany, NW")
    expect(entry.data).to_equal({"country": "DE", "province": "NW"})


@test
async def reconfigure_with_categories(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow with categories."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unites States, TX",
        data={"country": "US", "province": "TX"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "AL", CONF_CATEGORIES: [UNOFFICIAL]},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.title).to_equal("United States, AL")
    expect(entry.data).to_equal({CONF_COUNTRY: "US", CONF_PROVINCE: "AL"})
    expect(entry.options).to_equal({CONF_CATEGORIES: ["unofficial"]})


@test
async def reconfigure_incorrect_language(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow default to English."""
    hass.config.language = "en-XX"

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Germany, BW",
        data={"country": "DE", "province": "BW"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "NW"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.title).to_equal("Germany, NW")
    expect(entry.data).to_equal({"country": "DE", "province": "NW"})


@test
async def reconfigure_entry_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow stops if other entry already exist."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Germany, BW",
        data={"country": "DE", "province": "BW"},
    )
    entry.add_to_hass(hass)
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="Germany, NW",
        data={"country": "DE", "province": "NW"},
    )
    entry2.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVINCE: "NW"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.title).to_equal("Germany, BW")
    expect(entry.data).to_equal({"country": "DE", "province": "BW"})


@test
async def form_with_options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the flow with configuring options."""
    await hass.config.async_set_time_zone("America/Chicago")
    zone = await dt_util.async_get_time_zone("America/Chicago")
    with freeze_time(datetime(2024, 10, 31, 12, 0, 0, tzinfo=zone)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_COUNTRY: "US"},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PROVINCE: "TX", CONF_CATEGORIES: [UNOFFICIAL]},
        )
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("United States, TX")
        expect(result["data"]).to_equal(
            {CONF_COUNTRY: "US", CONF_PROVINCE: "TX"}
        )
        expect(result["options"]).to_equal({CONF_CATEGORIES: ["unofficial"]})

        state = hass.states.get("calendar.united_states_tx")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal(STATE_ON)

        entries = hass.config_entries.async_entries(DOMAIN)
        entry = entries[0]
        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_CATEGORIES: []},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_CATEGORIES: []})

        state = hass.states.get("calendar.united_states_tx")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal(STATE_OFF)


@test
async def options_abort_no_categories(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the options flow abort if no categories to select."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_COUNTRY: "AL"},
        title="Albania",
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_categories")
