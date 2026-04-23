"""Test the MyPermobil config flow."""

from __future__ import annotations

from unittest.mock import Mock, patch

from mypermobil import (
    MyPermobilAPIException,
    MyPermobilClientException,
    MyPermobilEulaException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.permobil import config_flow
from homeassistant.const import CONF_CODE, CONF_EMAIL, CONF_REGION, CONF_TOKEN, CONF_TTL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import MOCK_REGION_NAME, MOCK_TOKEN, MOCK_URL

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import mock_setup_entry as mock_setup_entry_fx, my_permobil as my_permobil_fx


MOCK_CODE = "012345"
MOCK_EMAIL = "valid@email.com"
INVALID_EMAIL = "this is not a valid email"
VALID_DATA = {
    CONF_EMAIL: MOCK_EMAIL,
    CONF_REGION: MOCK_URL,
    CONF_CODE: MOCK_CODE,
    CONF_TOKEN: MOCK_TOKEN[0],
    CONF_TTL: MOCK_TOKEN[1],
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: Mock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network and mock_setup_entry for every test."""


@test
async def successful_config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test the config flow from start to finish with no errors."""
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(VALID_DATA)


@test
async def config_flow_incorrect_code(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test email code verification with API error."""
    my_permobil.request_application_token.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]["base"]).to_equal("invalid_code")


@test
async def config_flow_unsigned_eula(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test email code verification with unsigned eula."""
    my_permobil.request_application_token.side_effect = MyPermobilEulaException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]["base"]).to_equal("unsigned_eula")

    with patch.object(
        my_permobil,
        "request_application_token",
        return_value=MOCK_TOKEN,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CODE: MOCK_CODE},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(VALID_DATA)


@test
async def config_flow_incorrect_region(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test when the user does not exist in the selected region."""
    my_permobil.request_application_code.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]["base"]).to_equal("code_request_error")


@test
async def config_flow_region_request_error(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test region request error."""
    my_permobil.request_region_names.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]["base"]).to_equal("region_fetch_error")


@test
async def config_flow_invalid_email(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test an incorrectly formatted email."""
    my_permobil.set_email.side_effect = MyPermobilClientException()
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: INVALID_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)
    expect(result["errors"]["base"]).to_equal("invalid_email")


@test
async def config_flow_reauth_success(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test the config flow reauth replacing values."""
    reauth_token = ("b" * 256, "reauth_date")
    reauth_code = "567890"
    my_permobil.request_application_token.return_value = reauth_token

    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: reauth_code},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(
        {
            CONF_EMAIL: MOCK_EMAIL,
            CONF_REGION: MOCK_URL,
            CONF_CODE: reauth_code,
            CONF_TOKEN: reauth_token[0],
            CONF_TTL: reauth_token[1],
        }
    )


@test
async def config_flow_reauth_fail_invalid_code(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test reauth flow when email code fails."""
    reauth_invalid_code = "567890"
    my_permobil.request_application_token.side_effect = MyPermobilAPIException
    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: reauth_invalid_code},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]["base"]).to_equal("invalid_code")


@test
async def config_flow_reauth_fail_code_request(
    hass: HomeAssistant = Depends(hass_fixture),
    my_permobil: Mock = Depends(my_permobil_fx),
) -> None:
    """Test the config flow reauth fails when code request fails."""
    my_permobil.request_application_code.side_effect = MyPermobilAPIException
    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=my_permobil,
    ):
        result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
