"""Test the SwitchBee Smart Home config flow."""

import json
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.switchbee.config_flow import SwitchBeeError
from homeassistant.components.switchbee.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_FAILED_TO_LOGIN_MSG, MOCK_INVALID_TOKEN_MGS

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("without_cucode", test_cucode_in_coordinator_data=False),
    test.case("with_cucode", test_cucode_in_coordinator_data=True),
)
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    test_cucode_in_coordinator_data: bool,
) -> None:
    """Test we get the form."""
    coordinator_data = json.loads(
        await async_load_fixture(hass, "switchbee.json", DOMAIN)
    )

    if test_cucode_in_coordinator_data:
        coordinator_data["data"]["cuCode"] = "300F123456"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "switchbee.api.polling.CentralUnitPolling.get_configuration",
            return_value=coordinator_data,
        ),
        patch(
            "homeassistant.components.switchbee.async_setup_entry",
            return_value=True,
        ),
        patch(
            "switchbee.api.polling.CentralUnitPolling.fetch_states", return_value=None
        ),
        patch("switchbee.api.polling.CentralUnitPolling._login", return_value=None),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "switchbee.api.polling.CentralUnitPolling._login",
        side_effect=SwitchBeeError(MOCK_FAILED_TO_LOGIN_MSG),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "switchbee.api.polling.CentralUnitPolling._login",
        side_effect=SwitchBeeError(MOCK_INVALID_TOKEN_MGS),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "switchbee.api.polling.CentralUnitPolling._login",
        side_effect=Exception,
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(form_result["type"]).to_be(FlowResultType.FORM)
    expect(form_result["errors"]).to_equal({"base": "unknown"})


@test
async def form_entry_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an already existing entry."""
    coordinator_data = json.loads(
        await async_load_fixture(hass, "switchbee.json", DOMAIN)
    )
    MockConfigEntry(
        unique_id="a8:21:08:e7:67:b6",
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
        title="1.1.1.1",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("switchbee.api.polling.CentralUnitPolling._login", return_value=None),
        patch(
            "homeassistant.components.switchbee.async_setup_entry",
            return_value=True,
        ),
        patch(
            "switchbee.api.polling.CentralUnitPolling.get_configuration",
            return_value=coordinator_data,
        ),
        patch(
            "switchbee.api.polling.CentralUnitPolling.fetch_states", return_value=None
        ),
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.2.2",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(form_result["type"]).to_be(FlowResultType.ABORT)
    expect(form_result["reason"]).to_equal("already_configured")
