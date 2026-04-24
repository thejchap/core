"""Test the Renault config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, PropertyMock, patch

import aiohttp
from renault_api.gigya.exceptions import InvalidCredentialsException
from renault_api.kamereon import schemas
from renault_api.renault_account import RenaultAccount
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.renault.const import (
    CONF_KAMEREON_ACCOUNT_ID,
    CONF_LOCALE,
    DOMAIN,
)
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import aiohttp_client

from ._fixtures import (
    config_entry as config_entry_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry, async_load_fixture, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network and mock_setup_entry for every test."""


@test.cases(
    test.case("unknown", exception=Exception, error="unknown"),
    test.case(
        "cannot_connect",
        exception=aiohttp.ClientConnectionError,
        error="cannot_connect",
    ),
    test.case(
        "invalid_credentials",
        exception=InvalidCredentialsException(403042, "invalid loginID or password"),
        error="invalid_credentials",
    ),
)
async def config_flow_single_account(
    *,
    exception: Exception | type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "renault_api.renault_session.RenaultSession.login",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    data_schema = result["data_schema"].schema
    expect(get_schema_suggested_value(data_schema, CONF_LOCALE)).to_equal("fr_FR")
    expect(get_schema_suggested_value(data_schema, CONF_USERNAME)).to_equal(
        "email@test.com"
    )
    expect(get_schema_suggested_value(data_schema, CONF_PASSWORD)).to_equal("test")

    renault_account = AsyncMock()
    type(renault_account).account_id = PropertyMock(return_value="account_id_1")
    renault_account.get_vehicles.return_value = (
        schemas.KamereonVehiclesResponseSchema.loads(
            await async_load_fixture(hass, "vehicle_zoe_40.json", DOMAIN)
        )
    )

    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_account.RenaultAccount.account_id", return_value="123"
        ),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("account_id_1")
    expect(result["data"][CONF_USERNAME]).to_equal("email@test.com")
    expect(result["data"][CONF_PASSWORD]).to_equal("test")
    expect(result["data"][CONF_KAMEREON_ACCOUNT_ID]).to_equal("account_id_1")
    expect(result["data"][CONF_LOCALE]).to_equal("fr_FR")
    expect(result["context"]["unique_id"]).to_equal("account_id_1")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_no_account(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("kamereon_no_account")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def config_flow_multiple_accounts(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test what happens if multiple Kamereon accounts are available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    renault_account_1 = RenaultAccount(
        "account_id_1",
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    renault_account_2 = RenaultAccount(
        "account_id_2",
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    renault_vehicles = schemas.KamereonVehiclesResponseSchema.loads(
        await async_load_fixture(hass, "renault/vehicle_zoe_40.json")
    )

    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account_1, renault_account_2],
        ),
        patch(
            "renault_api.renault_account.RenaultAccount.get_vehicles",
            return_value=renault_vehicles,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("kamereon")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_KAMEREON_ACCOUNT_ID: "account_id_2"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("account_id_2")
    expect(result["data"][CONF_USERNAME]).to_equal("email@test.com")
    expect(result["data"][CONF_PASSWORD]).to_equal("test")
    expect(result["data"][CONF_KAMEREON_ACCOUNT_ID]).to_equal("account_id_2")
    expect(result["data"][CONF_LOCALE]).to_equal("fr_FR")
    expect(result["context"]["unique_id"]).to_equal("account_id_2")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test abort if unique_id configured."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    renault_account = RenaultAccount(
        "account_id_1",
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    renault_vehicles = schemas.KamereonVehiclesResponseSchema.loads(
        await async_load_fixture(hass, "renault/vehicle_zoe_50.json")
    )
    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account],
        ),
        patch(
            "renault_api.renault_account.RenaultAccount.get_vehicles",
            return_value=renault_vehicles,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test the start of the config flow."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]).to_equal(
        {CONF_NAME: "Mock Title", CONF_USERNAME: "email@test.com"}
    )
    expect(result["errors"]).to_equal({})

    with patch(
        "renault_api.renault_session.RenaultSession.login",
        side_effect=InvalidCredentialsException(403042, "invalid loginID or password"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "any"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["description_placeholders"]).to_equal(
        {CONF_NAME: "Mock Title", CONF_USERNAME: "email@test.com"}
    )
    expect(result2["errors"]).to_equal({"base": "invalid_credentials"})

    with patch("renault_api.renault_session.RenaultSession.login"):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "any"},
        )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("email@test.com")
    expect(entry.data[CONF_PASSWORD]).to_equal("any")


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test reconfigure works."""
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    data_schema = result["data_schema"].schema
    expect(get_schema_suggested_value(data_schema, CONF_LOCALE)).to_equal("fr_FR")
    expect(get_schema_suggested_value(data_schema, CONF_USERNAME)).to_equal(
        "email@test.com"
    )
    expect(get_schema_suggested_value(data_schema, CONF_PASSWORD)).to_equal("test")

    renault_account = AsyncMock()
    type(renault_account).account_id = PropertyMock(return_value="account_id_1")
    renault_account.get_vehicles.return_value = (
        schemas.KamereonVehiclesResponseSchema.loads(
            await async_load_fixture(hass, "vehicle_zoe_40.json", DOMAIN)
        )
    )

    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_account.RenaultAccount.account_id", return_value="123"
        ),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email2@test.com",
                CONF_PASSWORD: "test2",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("email2@test.com")
    expect(entry.data[CONF_PASSWORD]).to_equal("test2")
    expect(entry.data[CONF_KAMEREON_ACCOUNT_ID]).to_equal("account_id_1")
    expect(entry.data[CONF_LOCALE]).to_equal("fr_FR")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reconfigure_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test reconfigure fails on account ID mismatch."""
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    data_schema = result["data_schema"].schema
    expect(get_schema_suggested_value(data_schema, CONF_LOCALE)).to_equal("fr_FR")
    expect(get_schema_suggested_value(data_schema, CONF_USERNAME)).to_equal(
        "email@test.com"
    )
    expect(get_schema_suggested_value(data_schema, CONF_PASSWORD)).to_equal("test")

    renault_account = AsyncMock()
    type(renault_account).account_id = PropertyMock(return_value="account_id_other")
    renault_account.get_vehicles.return_value = (
        schemas.KamereonVehiclesResponseSchema.loads(
            await async_load_fixture(hass, "vehicle_zoe_40.json", DOMAIN)
        )
    )

    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_account.RenaultAccount.account_id", return_value="1234"
        ),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email2@test.com",
                CONF_PASSWORD: "test2",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(entry.data[CONF_USERNAME]).to_equal("email@test.com")
    expect(entry.data[CONF_PASSWORD]).to_equal("test")
    expect(entry.data[CONF_KAMEREON_ACCOUNT_ID]).to_equal("account_id_1")
    expect(entry.data[CONF_LOCALE]).to_equal("fr_FR")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
