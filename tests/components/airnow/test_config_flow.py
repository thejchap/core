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

from ._fixtures import config, config_entry, options, setup_airnow

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_airnow),
    config: dict[str, Any] = Depends(config),
    options: dict[str, Any] = Depends(options),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["description_placeholders"]).to_equal(
        {"api_key_url": "https://docs.airnowapi.org/account/request/"}
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], config)
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(config)
    expect(result2["options"]).to_equal(options)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle invalid auth."""
    with (
        patch("pyairnow.WebServiceAPI._get", AsyncMock(side_effect=InvalidKeyError)),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_invalid_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle invalid location."""
    with (
        patch("pyairnow.WebServiceAPI._get", AsyncMock(return_value={})),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_location"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle cannot connect error."""
    with (
        patch("pyairnow.WebServiceAPI._get", AsyncMock(side_effect=AirNowError)),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_empty_result(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle empty response error."""
    with (
        patch(
            "pyairnow.WebServiceAPI._get", AsyncMock(side_effect=EmptyResponseError)
        ),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_location"})


@test
async def form_unexpected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test we handle an unexpected error."""
    with (
        patch("pyairnow.WebServiceAPI._get", AsyncMock(side_effect=RuntimeError)),
        patch("homeassistant.components.airnow.PLATFORMS", []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(config_entry),
    config: dict[str, Any] = Depends(config),
) -> None:
    """Test that the form aborts if the Lat/Lng is already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], config)
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def config_migration_v2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_airnow),
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

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(config_entry.version).to_equal(2)
    expect(config_entry.data.get(CONF_RADIUS)).to_be_falsy()
    expect(config_entry.options.get(CONF_RADIUS)).to_equal(25)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_airnow),
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

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
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

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_RADIUS: 25})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
