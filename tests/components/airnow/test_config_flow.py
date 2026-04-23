"""Test the AirNow config flow."""

from typing import Any
from unittest.mock import AsyncMock, patch

from pyairnow.errors import AirNowError, EmptyResponseError, InvalidKeyError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airnow.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.airnow._fixtures import (
    config,
    config_entry,
    data,
    mock_api_get,
    options,
    setup_airnow,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _setup_airnow: None = Depends(setup_airnow),
    config: dict[str, Any] = Depends(config),
    options: dict[str, Any] = Depends(options),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})
    expect(result["description_placeholders"]).to_equal(
        {"api_key_url": "https://docs.airnowapi.org/account/request/"}
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], config)
    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["data"]).to_equal(config)
    expect(result2["options"]).to_equal(options)


@test.cases(
    test.case("invalid_auth", InvalidKeyError, "invalid_auth"),
    test.case("cannot_connect", AirNowError, "cannot_connect"),
    test.case("empty_result", EmptyResponseError, "invalid_location"),
    test.case("unknown", RuntimeError, "unknown"),
)
async def form_api_errors(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle API errors surfaced through the config flow."""
    mock_api_get_err = AsyncMock(side_effect=side_effect)
    with (
        patch("pyairnow.WebServiceAPI._get", mock_api_get_err),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": error})


@test
async def form_invalid_location(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _setup_airnow: None = Depends(setup_airnow),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle invalid location (empty response data)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("pyairnow.WebServiceAPI._get", AsyncMock(return_value=[])):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "invalid_location"})


@test
async def entry_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _config_entry: MockConfigEntry = Depends(config_entry),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test that the form aborts if the Lat/Lng is already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], config)
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def config_migration_v2(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _setup_airnow: None = Depends(setup_airnow),
) -> None:
    """Test that the config migration from Version 1 to Version 2 works."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="AirNow",
        data={
            CONF_API_KEY: "1234",
            CONF_LATITUDE: 33.6,
            CONF_LONGITUDE: -118.1,
            CONF_RADIUS: 25,
        },
        source=config_entries.SOURCE_USER,
        options={CONF_RADIUS: 10},
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.version).to_equal(2)
    expect(not config_entry.data.get(CONF_RADIUS)).to_be(True)
    expect(config_entry.options.get(CONF_RADIUS)).to_equal(25)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _setup_airnow: None = Depends(setup_airnow),
) -> None:
    """Test that the options flow works."""
    config_entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        title="AirNow",
        data={
            CONF_API_KEY: "1234",
            CONF_LATITUDE: 33.6,
            CONF_LONGITUDE: -118.1,
        },
        source=config_entries.SOURCE_USER,
        options={CONF_RADIUS: 10},
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    with patch(
        "homeassistant.components.airnow.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_RADIUS: 25},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(config_entry.options).to_equal({CONF_RADIUS: 25})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
