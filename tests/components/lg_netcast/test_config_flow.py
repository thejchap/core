"""Define tests for the LG Netcast config flow."""

from datetime import timedelta
from unittest.mock import DEFAULT, patch

from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.components.lg_netcast.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_ID,
    CONF_MODEL,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant

from . import (
    FAKE_PIN,
    FRIENDLY_NAME,
    IP_ADDRESS,
    MODEL_NAME,
    UNIQUE_ID,
    _patch_lg_netcast,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def user_invalid_host(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that errors are shown when the host is invalid."""
    with _patch_lg_netcast():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "invalid/host"}
        )

        expect(result["errors"]).to_equal({CONF_HOST: "invalid_host"})


@test
async def manual_host(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("authorize")
        expect(bool(result["errors"])).to_be(False)

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result2["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("authorize")
        expect(result2["errors"]).not_.to_be(None)
        expect(result2["errors"][CONF_ACCESS_TOKEN]).to_equal("invalid_access_token")

        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ACCESS_TOKEN: FAKE_PIN}
        )

        expect(result3["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(FRIENDLY_NAME)
        expect(result3["data"]).to_equal(
            {
                CONF_HOST: IP_ADDRESS,
                CONF_ACCESS_TOKEN: FAKE_PIN,
                CONF_NAME: FRIENDLY_NAME,
                CONF_MODEL: MODEL_NAME,
                CONF_ID: UNIQUE_ID,
            }
        )


@test
async def manual_host_no_connection_during_authorize(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast(fail_connection=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def manual_host_invalid_details_during_authorize(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast(invalid_details=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def manual_host_unsuccessful_details_response(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast(always_404=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def manual_host_no_unique_id_response(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual host configuration."""
    with _patch_lg_netcast(no_unique_id=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
        expect(result["reason"]).to_equal("invalid_host")


@test
async def invalid_session_id(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test Invalid Session ID."""
    with _patch_lg_netcast(session_error=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("authorize")
        expect(bool(result["errors"])).to_be(False)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ACCESS_TOKEN: FAKE_PIN}
        )

        expect(result2["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("authorize")
        expect(result2["errors"]).not_.to_be(None)
        expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def display_access_token_aborted(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Access token display is cancelled."""

    def _async_track_time_interval(
        hass: HomeAssistant,
        action,
        interval: timedelta,
        *,
        name=None,
        cancel_on_shutdown=None,
    ):
        hass.async_create_task(action())
        return DEFAULT

    with (
        _patch_lg_netcast(session_error=True),
        patch(
            "homeassistant.components.lg_netcast.config_flow.async_track_time_interval"
        ) as mock_interval,
    ):
        mock_interval.side_effect = _async_track_time_interval
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: IP_ADDRESS}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("authorize")
        expect(bool(result["errors"])).to_be(False)

        expect(mock_interval.called).to_be(True)

        hass.config_entries.flow.async_abort(result["flow_id"])
        expect(mock_interval.return_value.called).to_be(True)
