"""Test the moehlenhoff_alpha2 config flow."""

from functools import partialmethod
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.moehlenhoff_alpha2.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_BASE_HOST, mock_update_data

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be_falsy()

    with (
        patch(
            "homeassistant.components.moehlenhoff_alpha2.config_flow.Alpha2Base.update_data",
            partialmethod(mock_update_data, hass),
        ),
        patch(
            "homeassistant.components.moehlenhoff_alpha2.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"host": MOCK_BASE_HOST},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Alpha2Test")
    expect(result2["data"]).to_equal({"host": MOCK_BASE_HOST})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_duplicate_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that errors are shown when duplicates are added."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": MOCK_BASE_HOST},
        source=config_entries.SOURCE_USER,
    )
    config_entry.add_to_hass(hass)

    expect(config_entry.data["host"]).to_equal(MOCK_BASE_HOST)

    with patch(
        "moehlenhoff_alpha2.Alpha2Base.update_data",
        partialmethod(mock_update_data, hass),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data={"host": MOCK_BASE_HOST},
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def form_cannot_connect_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("moehlenhoff_alpha2.Alpha2Base.update_data", side_effect=TimeoutError):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"host": MOCK_BASE_HOST},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unexpected_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test unexpected error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("moehlenhoff_alpha2.Alpha2Base.update_data", side_effect=Exception):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"host": MOCK_BASE_HOST},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "unknown"})
