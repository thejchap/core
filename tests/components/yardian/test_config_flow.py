"""Test the Yardian config flow."""

from unittest.mock import AsyncMock, patch

from pyyardian import NetworkException, NotAuthorizedException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.yardian.const import DOMAIN, PRODUCT_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        return_value={"name": "fake_name", "yid": "fake_yid"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(PRODUCT_NAME)
    expect(result2["data"]).to_equal(
        {
            "host": "fake_host",
            "access_token": "fake_token",
            "name": "fake_name",
            "yid": "fake_yid",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        side_effect=NotAuthorizedException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        return_value={"name": "fake_name", "yid": "fake_yid"},
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(PRODUCT_NAME)
    expect(result3["data"]).to_equal(
        {
            "host": "fake_host",
            "access_token": "fake_token",
            "name": "fake_name",
            "yid": "fake_yid",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        side_effect=NetworkException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        return_value={"name": "fake_name", "yid": "fake_yid"},
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(PRODUCT_NAME)
    expect(result3["data"]).to_equal(
        {
            "host": "fake_host",
            "access_token": "fake_token",
            "name": "fake_name",
            "yid": "fake_yid",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_uncategorized_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle uncategorized error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    with patch(
        "homeassistant.components.yardian.config_flow.AsyncYardianClient.fetch_device_info",
        return_value={"name": "fake_name", "yid": "fake_yid"},
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "fake_host",
                "access_token": "fake_token",
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(PRODUCT_NAME)
    expect(result3["data"]).to_equal(
        {
            "host": "fake_host",
            "access_token": "fake_token",
            "name": "fake_name",
            "yid": "fake_yid",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
