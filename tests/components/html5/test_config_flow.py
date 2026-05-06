"""Test the HTML5 config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.html5.const import (
    ATTR_VAPID_EMAIL,
    ATTR_VAPID_PRV_KEY,
    ATTR_VAPID_PUB_KEY,
    DOMAIN,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from ._fixtures import MOCK_CONF, MOCK_CONF_PUB_KEY

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def step_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful user config flow."""
    with patch(
        "homeassistant.components.html5.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONF.copy(),
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_be(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(
            {
                ATTR_VAPID_PRV_KEY: MOCK_CONF[ATTR_VAPID_PRV_KEY],
                ATTR_VAPID_PUB_KEY: MOCK_CONF_PUB_KEY,
                ATTR_VAPID_EMAIL: MOCK_CONF[ATTR_VAPID_EMAIL],
                CONF_NAME: DOMAIN,
            }
        )

        expect(mock_setup_entry.call_count).to_equal(1)


@test
async def step_user_success_generate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful user config flow, generating a key pair."""
    with patch(
        "homeassistant.components.html5.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        conf = {ATTR_VAPID_EMAIL: MOCK_CONF[ATTR_VAPID_EMAIL]}
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=conf
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_be(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(result["data"][ATTR_VAPID_EMAIL]).to_equal(MOCK_CONF[ATTR_VAPID_EMAIL])

        expect(mock_setup_entry.call_count).to_equal(1)


@test
async def step_user_new_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test new user input."""
    with patch(
        "homeassistant.components.html5.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_be(data_entry_flow.FlowResultType.FORM)
        expect(mock_setup_entry.call_count).to_equal(0)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONF
        )
        expect(result["type"]).to_be(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(mock_setup_entry.call_count).to_equal(1)


@test.cases(
    test.case("invalid_prv_key", key=ATTR_VAPID_PRV_KEY, value="invalid"),
)
async def step_user_form_invalid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    key: str,
    value: str,
) -> None:
    """Test invalid user input."""
    with patch(
        "homeassistant.components.html5.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        bad_conf = MOCK_CONF.copy()
        bad_conf[key] = value

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=bad_conf
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(mock_setup_entry.call_count).to_equal(0)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONF
        )
        expect(result["type"]).to_be(data_entry_flow.FlowResultType.CREATE_ENTRY)
        expect(mock_setup_entry.call_count).to_equal(1)
