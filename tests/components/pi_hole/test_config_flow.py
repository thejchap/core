"""Test pi_hole config flow."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components import pi_hole
from homeassistant.components.pi_hole.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    CONFIG_DATA_DEFAULTS,
    CONFIG_ENTRY_WITH_API_KEY,
    CONFIG_FLOW_USER,
    FTL_ERROR,
    NAME,
    ZERO_DATA,
    _create_mocked_hole,
    _patch_config_flow_hole,
    _patch_init_hole,
    _patch_setup_hole,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def flow_user_with_api_key_v6(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with api key needed."""
    mocked_hole = _create_mocked_hole(has_data=False, api_version=6)
    with (
        _patch_init_hole(mocked_hole),
        _patch_config_flow_hole(mocked_hole),
        _patch_setup_hole() as mock_setup,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={**CONFIG_FLOW_USER, CONF_API_KEY: "invalid_password"},
        )
        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_auth"})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG_FLOW_USER,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(CONFIG_ENTRY_WITH_API_KEY)
        mock_setup.assert_called_once()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_FLOW_USER,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_with_api_key_v5(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with api key needed."""
    mocked_hole = _create_mocked_hole(api_version=5)
    with (
        _patch_init_hole(mocked_hole),
        _patch_config_flow_hole(mocked_hole),
        _patch_setup_hole() as mock_setup,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={**CONFIG_FLOW_USER, CONF_API_KEY: "wrong_token"},
        )

        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_auth"})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG_FLOW_USER,
        )

        expect(mocked_hole.instances[-1].data).to_equal(ZERO_DATA)

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(NAME)
        expect(result["data"]).to_equal({**CONFIG_ENTRY_WITH_API_KEY})
        mock_setup.assert_called_once()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_FLOW_USER,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_invalid(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with completely invalid server."""
    mocked_hole = _create_mocked_hole(raise_exception=True)
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_FLOW_USER
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"api_key": "invalid_auth"})


@test
async def flow_user_invalid_v6(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with invalid server - typically a V6 API and a incorrect app password."""
    mocked_hole = _create_mocked_hole(
        has_data=True, api_version=6, incorrect_app_password=True
    )
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_FLOW_USER
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"api_key": "invalid_auth"})


@test
async def flow_reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth flow."""
    mocked_hole = _create_mocked_hole(has_data=False, api_version=5)
    entry = MockConfigEntry(
        domain=pi_hole.DOMAIN,
        data={**CONFIG_DATA_DEFAULTS, CONF_API_KEY: "oldkey"},
    )
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole), _patch_config_flow_hole(mocked_hole):
        expect(bool(await hass.config_entries.async_setup(entry.entry_id))).to_be(False)
        await hass.async_block_till_done()

        flows = hass.config_entries.flow.async_progress()

        expect(len(flows)).to_equal(1)
        expect(flows[0]["step_id"]).to_equal("reauth_confirm")
        expect(flows[0]["context"]["entry_id"]).to_equal(entry.entry_id)
        mocked_hole.instances[-1].api_token = "newkey"
        result = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            user_input={CONF_API_KEY: "newkey"},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(entry.data[CONF_API_KEY]).to_equal("newkey")


@test
async def flow_user_invalid_host(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with invalid server host address."""
    mocked_hole = _create_mocked_hole(api_version=6, wrong_host=True)
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_FLOW_USER
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_error_response(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow but dataotherbase errors occur."""
    mocked_hole = _create_mocked_hole(api_version=5, ftl_error=True, has_data=False)
    with _patch_config_flow_hole(mocked_hole), _patch_init_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_FLOW_USER
        )
        expect(mocked_hole.instances[-1].data).to_equal(FTL_ERROR)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})
