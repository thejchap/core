"""Test the MyPermobil config flow."""

from unittest.mock import AsyncMock, Mock, patch

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

from ._fixtures import my_permobil, mock_setup_entry
from .const import MOCK_REGION_NAME, MOCK_TOKEN, MOCK_URL

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

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
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Anchor fixture (mock_setup_entry autouse equivalent)."""


@test
async def successful_config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test the config flow from start to finish with no errors."""
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test email code verification with API error."""
    permobil.request_application_token.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test email code verification with unsigned eula error."""
    permobil.request_application_token.side_effect = MyPermobilEulaException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: MOCK_CODE},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("email_code")
    expect(result["errors"]["base"]).to_equal("unsigned_eula")

    with patch.object(
        permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test when the user does not exist in the selected region."""
    permobil.request_application_code.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_EMAIL: MOCK_EMAIL},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: MOCK_REGION_NAME},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("region")
    expect(result["errors"]["base"]).to_equal("code_request_error")


@test
async def config_flow_region_request_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test region request error."""
    permobil.request_region_names.side_effect = MyPermobilAPIException
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test an incorrectly formatted email."""
    permobil.set_email.side_effect = MyPermobilClientException()
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test the config flow reauth - replace values."""
    reauth_token = ("b" * 256, "reauth_date")
    reauth_code = "567890"
    permobil.request_application_token.return_value = reauth_token

    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test the config flow reauth when the email code fails."""
    reauth_invalid_code = "567890"
    permobil.request_application_token.side_effect = MyPermobilAPIException
    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    permobil: Mock = Depends(my_permobil),
) -> None:
    """Test the config flow reauth code request fails."""
    permobil.request_application_code.side_effect = MyPermobilAPIException
    mock_entry = MockConfigEntry(domain="permobil", data=VALID_DATA)
    mock_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.permobil.config_flow.MyPermobil",
        return_value=permobil,
    ):
        result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
