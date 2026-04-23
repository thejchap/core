"""Test the FiveM config flow."""

from unittest.mock import patch

from fivem import FiveMServerOfflineError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fivem.config_flow import DEFAULT_PORT
from homeassistant.components.fivem.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture

USER_INPUT = {
    CONF_HOST: "fivem.dummyserver.com",
    CONF_PORT: DEFAULT_PORT,
}


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


def _mock_fivem_info_success():
    return {
        "resources": ["fivem", "monitor"],
        "server": "FXServer-dummy v0.0.0.DUMMY linux",
        "vars": {"gamename": "gta5"},
        "version": 123456789,
    }


def _mock_fivem_info_invalid():
    return {
        "plugins": ["sample"],
        "data": {"gamename": "gta5"},
    }


def _mock_fivem_info_invalid_game_name():
    info = _mock_fivem_info_success()
    info["vars"]["gamename"] = "redm"
    return info


@test
async def show_config_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test if initial configuration form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "fivem.fivem.FiveM.get_info_raw",
            return_value=_mock_fivem_info_success(),
        ),
        patch(
            "homeassistant.components.fivem.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(USER_INPUT[CONF_HOST])
    expect(result2["data"]).to_equal(USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "fivem.fivem.FiveM.get_info_raw",
        side_effect=FiveMServerOfflineError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_invalid(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "fivem.fivem.FiveM.get_info_raw",
        return_value=_mock_fivem_info_invalid(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_invalid_game_name(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "fivem.fivem.FiveM.get_info_raw",
        return_value=_mock_fivem_info_invalid_game_name(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_game_name"})
