"""Test the MetOffice config flow."""

import json
from unittest.mock import patch

import requests_mock as requests_mock_lib
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.metoffice.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr

from ._fixtures import mock_simple_manager_fail, requests_mock
from .const import (
    METOFFICE_CONFIG_WAVERTREE,
    TEST_API_KEY,
    TEST_LATITUDE_WAVERTREE,
    TEST_LONGITUDE_WAVERTREE,
    TEST_SITE_NAME_WAVERTREE,
)

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rmock: requests_mock_lib.Mocker = Depends(requests_mock),
) -> None:
    """Test we get the form."""
    hass.config.latitude = TEST_LATITUDE_WAVERTREE
    hass.config.longitude = TEST_LONGITUDE_WAVERTREE

    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.metoffice.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": TEST_API_KEY}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_SITE_NAME_WAVERTREE)
    expect(result2["data"]).to_equal(
        {
            "api_key": TEST_API_KEY,
            "latitude": TEST_LATITUDE_WAVERTREE,
            "longitude": TEST_LONGITUDE_WAVERTREE,
            "name": TEST_SITE_NAME_WAVERTREE,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rmock: requests_mock_lib.Mocker = Depends(requests_mock),
) -> None:
    """Test we handle duplicate entries."""
    hass.config.latitude = TEST_LATITUDE_WAVERTREE
    hass.config.longitude = TEST_LONGITUDE_WAVERTREE

    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )

    MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{TEST_LATITUDE_WAVERTREE}_{TEST_LONGITUDE_WAVERTREE}",
        data=METOFFICE_CONFIG_WAVERTREE,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=METOFFICE_CONFIG_WAVERTREE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rmock: requests_mock_lib.Mocker = Depends(requests_mock),
) -> None:
    """Test we handle cannot connect error."""
    hass.config.latitude = TEST_LATITUDE_WAVERTREE
    hass.config.longitude = TEST_LONGITUDE_WAVERTREE

    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily", text=""
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": TEST_API_KEY},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    manager_fail=Depends(mock_simple_manager_fail),
) -> None:
    """Test we handle unknown error."""
    mock_instance = manager_fail.return_value
    mock_instance.get_forecast.side_effect = ValueError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": TEST_API_KEY},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rmock: requests_mock_lib.Mocker = Depends(requests_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test handling authentication errors and reauth flow."""
    freezer.move_to("2024-11-23T12:00:00+00:00")
    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=wavertree_hourly,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(len(device_registry.devices)).to_equal(1)

    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text="",
        status_code=401,
    )
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text="",
        status_code=401,
    )

    await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"],
        {CONF_API_KEY: TEST_API_KEY},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )
    rmock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=wavertree_hourly,
    )

    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"],
        {CONF_API_KEY: TEST_API_KEY},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
