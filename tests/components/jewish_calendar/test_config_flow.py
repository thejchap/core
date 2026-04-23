"""Test the Jewish calendar config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.jewish_calendar.const import (
    CONF_CANDLE_LIGHT_MINUTES,
    CONF_DIASPORA,
    CONF_HAVDALAH_OFFSET_MINUTES,
    DEFAULT_CANDLE_LIGHT,
    DEFAULT_DIASPORA,
    DEFAULT_LANGUAGE,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_TIME_ZONE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import config_entry, mock_setup_entry

from tests.common import MockConfigEntry
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
async def step_user(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DIASPORA: DEFAULT_DIASPORA, CONF_LANGUAGE: DEFAULT_LANGUAGE},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    await hass.async_block_till_done()
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].data[CONF_DIASPORA]).to_equal(DEFAULT_DIASPORA)
    expect(entries[0].data[CONF_LANGUAGE]).to_equal(DEFAULT_LANGUAGE)
    expect(entries[0].data[CONF_LATITUDE]).to_equal(hass.config.latitude)
    expect(entries[0].data[CONF_LONGITUDE]).to_equal(hass.config.longitude)
    expect(entries[0].data[CONF_ELEVATION]).to_equal(hass.config.elevation)
    expect(entries[0].data[CONF_TIME_ZONE]).to_equal(hass.config.time_zone)


@test
async def single_instance_allowed(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we abort if already setup."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def options(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test updating options."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_CANDLE_LIGHT_MINUTES: 25,
            CONF_HAVDALAH_OFFSET_MINUTES: 34,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].options[CONF_CANDLE_LIGHT_MINUTES]).to_equal(25)
    expect(entries[0].options[CONF_HAVDALAH_OFFSET_MINUTES]).to_equal(34)


@test
async def options_reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that updating the options triggers a value update."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(CONF_CANDLE_LIGHT_MINUTES not in config_entry.options).to_be(True)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CANDLE_LIGHT_MINUTES: DEFAULT_CANDLE_LIGHT + 1},
    )

    expect(config_entry.options[CONF_CANDLE_LIGHT_MINUTES]).to_equal(
        DEFAULT_CANDLE_LIGHT + 1
    )


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test starting a reconfigure flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_DIASPORA: not DEFAULT_DIASPORA},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_DIASPORA] is not DEFAULT_DIASPORA).to_be(True)
