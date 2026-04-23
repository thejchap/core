"""Test the Epic Games Store config flow."""

from http.client import HTTPException
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.epic_games_store.config_flow import get_default_language
from homeassistant.components.epic_games_store.const import DOMAIN
from homeassistant.const import CONF_COUNTRY, CONF_LANGUAGE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.epic_games_store._fixtures import mock_zeroconf
from tests.components.epic_games_store.const import (
    DATA_ERROR_ATTRIBUTE_NOT_FOUND,
    DATA_ERROR_WRONG_COUNTRY,
    DATA_FREE_GAMES,
    MOCK_COUNTRY,
    MOCK_LANGUAGE,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def default_language(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    hass.config.language = "fr"
    hass.config.country = "FR"
    expect(get_default_language(hass)).to_equal("fr")

    hass.config.language = "es"
    hass.config.country = "ES"
    expect(get_default_language(hass)).to_equal("es-ES")

    hass.config.language = "en"
    hass.config.country = "AZ"
    expect(get_default_language(hass) is None).to_be(True)


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        return_value=DATA_FREE_GAMES,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANGUAGE: MOCK_LANGUAGE,
                CONF_COUNTRY: MOCK_COUNTRY,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["result"].unique_id).to_equal(
        f"freegames-{MOCK_LANGUAGE}-{MOCK_COUNTRY}"
    )
    expect(result2["title"]).to_equal(
        f"Epic Games Store - Free Games ({MOCK_LANGUAGE}-{MOCK_COUNTRY})"
    )
    expect(result2["data"]).to_equal(
        {
            CONF_LANGUAGE: MOCK_LANGUAGE,
            CONF_COUNTRY: MOCK_COUNTRY,
        }
    )


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        side_effect=HTTPException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANGUAGE: MOCK_LANGUAGE,
                CONF_COUNTRY: MOCK_COUNTRY,
            },
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_cannot_connect_wrong_param(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        return_value=DATA_ERROR_WRONG_COUNTRY,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANGUAGE: MOCK_LANGUAGE,
                CONF_COUNTRY: MOCK_COUNTRY,
            },
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_service_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle service error gracefully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        return_value=DATA_ERROR_ATTRIBUTE_NOT_FOUND,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LANGUAGE: MOCK_LANGUAGE,
                CONF_COUNTRY: MOCK_COUNTRY,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["result"].unique_id).to_equal(
        f"freegames-{MOCK_LANGUAGE}-{MOCK_COUNTRY}"
    )
    expect(result2["title"]).to_equal(
        f"Epic Games Store - Free Games ({MOCK_LANGUAGE}-{MOCK_COUNTRY})"
    )
    expect(result2["data"]).to_equal(
        {
            CONF_LANGUAGE: MOCK_LANGUAGE,
            CONF_COUNTRY: MOCK_COUNTRY,
        }
    )
