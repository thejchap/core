"""Test Anova config flow."""

from unittest.mock import patch

from anova_wifi import AnovaApi, InvalidLogin
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.anova.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.anova._fixtures import anova_api
from tests.hass_fixtures import hass, mock_network

from . import CONF_INPUT


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _anova_api: AnovaApi = Depends(anova_api),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONF_INPUT,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(
        {CONF_USERNAME: "sample@gmail.com", CONF_PASSWORD: "sample"}
    )


@test
async def flow_wrong_login(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test incorrect login throwing error."""
    with patch(
        "homeassistant.components.anova.config_flow.AnovaApi.authenticate",
        side_effect=InvalidLogin,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def flow_unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test unknown error throwing error."""
    with patch(
        "homeassistant.components.anova.config_flow.AnovaApi.authenticate",
        side_effect=Exception(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": "unknown"})
