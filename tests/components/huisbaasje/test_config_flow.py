"""Test the Huisbaasje config flow."""

from unittest.mock import patch

from energyflip import (
    EnergyFlipConnectionException,
    EnergyFlipException,
    EnergyFlipUnauthenticatedException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.huisbaasje.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "energyflip.EnergyFlip.authenticate", return_value=None
        ) as mock_authenticate,
        patch(
            "energyflip.EnergyFlip.customer_overview", return_value=None
        ) as mock_customer_overview,
        patch(
            "energyflip.EnergyFlip.get_user_id",
            return_value="test-id",
        ) as mock_get_user_id,
        patch(
            "homeassistant.components.huisbaasje.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(form_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(form_result["title"]).to_equal("test-username")
    expect(form_result["data"]).to_equal(
        {
            "id": "test-id",
            "username": "test-username",
            "password": "test-password",
        }
    )
    expect(len(mock_authenticate.mock_calls)).to_equal(1)
    expect(len(mock_customer_overview.mock_calls)).to_equal(1)
    expect(len(mock_get_user_id.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth", side_effect=EnergyFlipException, base_error="invalid_auth"
    ),
    test.case(
        "cannot_connect",
        side_effect=EnergyFlipConnectionException,
        base_error="cannot_connect",
    ),
    test.case("unknown", side_effect=Exception, base_error="unknown"),
)
async def form_authenticate_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    base_error: str,
) -> None:
    """Test we handle errors in authenticate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "energyflip.EnergyFlip.authenticate",
        side_effect=side_effect,
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(form_result["type"]).to_be(FlowResultType.FORM)
    expect(form_result["errors"]).to_equal({"base": base_error})


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=EnergyFlipConnectionException,
        base_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        side_effect=EnergyFlipUnauthenticatedException,
        base_error="invalid_auth",
    ),
    test.case("unknown", side_effect=Exception, base_error="unknown"),
)
async def form_customer_overview_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    base_error: str,
) -> None:
    """Test we handle errors in customer_overview."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("energyflip.EnergyFlip.authenticate", return_value=None),
        patch(
            "energyflip.EnergyFlip.customer_overview",
            side_effect=side_effect,
        ),
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(form_result["type"]).to_be(FlowResultType.FORM)
    expect(form_result["errors"]).to_equal({"base": base_error})


@test
async def form_entry_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an already existing entry."""
    MockConfigEntry(
        unique_id="test-id",
        domain=DOMAIN,
        data={
            "id": "test-id",
            "username": "test-username",
            "password": "test-password",
        },
        title="test-username",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("energyflip.EnergyFlip.authenticate", return_value=None),
        patch("energyflip.EnergyFlip.customer_overview", return_value=None),
        patch(
            "energyflip.EnergyFlip.get_user_id",
            return_value="test-id",
        ),
        patch(
            "homeassistant.components.huisbaasje.async_setup_entry",
            return_value=True,
        ),
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    expect(form_result["type"]).to_be(FlowResultType.ABORT)
    expect(form_result["reason"]).to_equal("already_configured")
