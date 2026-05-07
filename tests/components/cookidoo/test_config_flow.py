"""Tryke ports of the Cookidoo config flow tests."""

from unittest.mock import AsyncMock

from cookidoo_api.exceptions import (
    CookidooAuthException,
    CookidooException,
    CookidooRequestException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.cookidoo.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_COUNTRY, CONF_EMAIL, CONF_LANGUAGE, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import (
    COUNTRY,
    EMAIL,
    LANGUAGE,
    PASSWORD,
    cookidoo_config_entry,
    mock_cookidoo_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


MOCK_DATA_USER_STEP = {
    CONF_EMAIL: EMAIL,
    CONF_PASSWORD: PASSWORD,
    CONF_COUNTRY: COUNTRY,
}

MOCK_DATA_LANGUAGE_STEP = {
    CONF_LANGUAGE: LANGUAGE,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


@test
async def flow_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_cookidoo_client),
) -> None:
    """Test we get the user flow and create entry with success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("cookidoo")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_LANGUAGE_STEP
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Cookidoo")
    expect(result["data"]).to_equal({**MOCK_DATA_USER_STEP, **MOCK_DATA_LANGUAGE_STEP})
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "request_exc", raise_error=CookidooRequestException(), text_error="cannot_connect"
    ),
    test.case(
        "auth_exc", raise_error=CookidooAuthException(), text_error="invalid_auth"
    ),
    test.case("generic_exc", raise_error=CookidooException(), text_error="unknown"),
    test.case("index_error", raise_error=IndexError(), text_error="unknown"),
)
async def flow_user_init_data_unknown_error_and_recover_on_step_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    client.login.side_effect = raise_error

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(text_error)

    client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_LANGUAGE_STEP
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].title).to_equal("Cookidoo")
    expect(result["data"]).to_equal({**MOCK_DATA_USER_STEP, **MOCK_DATA_LANGUAGE_STEP})


@test.cases(
    test.case(
        "request_exc", raise_error=CookidooRequestException(), text_error="cannot_connect"
    ),
    test.case(
        "auth_exc", raise_error=CookidooAuthException(), text_error="invalid_auth"
    ),
    test.case("generic_exc", raise_error=CookidooException(), text_error="unknown"),
    test.case("index_error", raise_error=IndexError(), text_error="unknown"),
)
async def flow_user_init_data_unknown_error_and_recover_on_step_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    client.get_additional_items.side_effect = raise_error

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_LANGUAGE_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(text_error)

    client.get_additional_items.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_LANGUAGE_STEP
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].title).to_equal("Cookidoo")
    expect(result["data"]).to_equal({**MOCK_DATA_USER_STEP, **MOCK_DATA_LANGUAGE_STEP})


@test
async def flow_user_init_data_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
) -> None:
    """Test we abort user data set when entry is already configured."""
    cfg_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_reconfigure_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
    client: AsyncMock = Depends(mock_cookidoo_client),
) -> None:
    """Test we get the reconfigure flow and create entry with success."""
    cfg_entry.add_to_hass(hass)
    await setup_integration(hass, cfg_entry)

    result = await cfg_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("cookidoo")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **MOCK_DATA_USER_STEP,
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: "DE",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: "de-DE"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(cfg_entry.data).to_equal(
        {
            **MOCK_DATA_USER_STEP,
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: "DE",
            CONF_LANGUAGE: "de-DE",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "request_exc", raise_error=CookidooRequestException(), text_error="cannot_connect"
    ),
    test.case("generic_exc", raise_error=CookidooException(), text_error="unknown"),
    test.case("index_error", raise_error=IndexError(), text_error="unknown"),
)
async def flow_reconfigure_init_data_unknown_error_and_recover_on_step_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
    client: AsyncMock = Depends(mock_cookidoo_client),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    client.login.side_effect = raise_error

    cfg_entry.add_to_hass(hass)
    await setup_integration(hass, cfg_entry)

    result = await cfg_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("cookidoo")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={**MOCK_DATA_USER_STEP, CONF_COUNTRY: "DE"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(text_error)

    client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={**MOCK_DATA_USER_STEP, CONF_COUNTRY: "DE"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: "de-DE"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(cfg_entry.data).to_equal(
        {
            **MOCK_DATA_USER_STEP,
            CONF_COUNTRY: "DE",
            CONF_LANGUAGE: "de-DE",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "request_exc", raise_error=CookidooRequestException(), text_error="cannot_connect"
    ),
    test.case("generic_exc", raise_error=CookidooException(), text_error="unknown"),
    test.case("index_error", raise_error=IndexError(), text_error="unknown"),
)
async def flow_reconfigure_init_data_unknown_error_and_recover_on_step_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
    client: AsyncMock = Depends(mock_cookidoo_client),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    client.get_additional_items.side_effect = raise_error

    cfg_entry.add_to_hass(hass)
    await setup_integration(hass, cfg_entry)

    result = await cfg_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["handler"]).to_equal("cookidoo")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={**MOCK_DATA_USER_STEP, CONF_COUNTRY: "DE"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("language")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: "de-DE"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(text_error)

    client.get_additional_items.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: "de-DE"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(cfg_entry.data).to_equal(
        {
            **MOCK_DATA_USER_STEP,
            CONF_COUNTRY: "DE",
            CONF_LANGUAGE: "de-DE",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reconfigure_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
) -> None:
    """Test we abort when the new config is not for the same user."""
    cfg_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(cfg_entry, unique_id="some_other_uuid")

    result = await cfg_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            **MOCK_DATA_USER_STEP,
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: "DE",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test
async def flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
) -> None:
    """Test reauth flow."""
    cfg_entry.add_to_hass(hass)

    result = await cfg_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(cfg_entry.data).to_equal(
        {
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: COUNTRY,
            CONF_LANGUAGE: LANGUAGE,
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "request_exc", raise_error=CookidooRequestException(), text_error="cannot_connect"
    ),
    test.case(
        "auth_exc", raise_error=CookidooAuthException(), text_error="invalid_auth"
    ),
    test.case("generic_exc", raise_error=CookidooException(), text_error="unknown"),
    test.case("index_error", raise_error=IndexError(), text_error="unknown"),
)
async def flow_reauth_error_and_recover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reauth flow."""
    cfg_entry.add_to_hass(hass)

    result = await cfg_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.login.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(cfg_entry.data).to_equal(
        {
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: COUNTRY,
            CONF_LANGUAGE: LANGUAGE,
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reauth_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_cookidoo_client),
    cfg_entry: MockConfigEntry = Depends(cookidoo_config_entry),
) -> None:
    """Test we abort when the new auth is not for the same user."""
    cfg_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(cfg_entry, unique_id="some_other_uuid")

    result = await cfg_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: "new-email", CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
