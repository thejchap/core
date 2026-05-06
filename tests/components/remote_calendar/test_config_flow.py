"""Test the Remote Calendar config flow."""

from httpx import HTTPError, InvalidURL, Response, TimeoutException
import respx
from tryke import Depends, expect, fixture, test

from homeassistant.components.remote_calendar.const import CONF_CALENDAR_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import (
    CALENDAR_NAME,
    CALENDER_URL,
    ics_content,
    mock_config_entry,
    set_time_zone,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _tz: None = Depends(set_time_zone),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form_import_ics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
) -> None:
    """Test we get the import form."""
    with respx.mock:
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(CALENDAR_NAME)
    expect(result2["data"]).to_equal(
        {
            CONF_CALENDAR_NAME: CALENDAR_NAME,
            CONF_URL: CALENDER_URL,
            CONF_VERIFY_SSL: True,
        }
    )


@test
async def form_import_webcal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
) -> None:
    """Test we get the import form."""
    with respx.mock:
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: "webcal://some.calendar.com/calendar.ics",
            },
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(CALENDAR_NAME)
    expect(result2["data"]).to_equal(
        {
            CONF_CALENDAR_NAME: CALENDAR_NAME,
            CONF_URL: CALENDER_URL,
            CONF_VERIFY_SSL: True,
        }
    )


@test.cases(
    test.case(
        "timeout",
        side_effect=TimeoutException("Connection timed out"),
        base_error="timeout_connect",
    ),
    test.case(
        "http_error",
        side_effect=HTTPError("Connection failed"),
        base_error="cannot_connect",
    ),
    test.case(
        "invalid_url_protocol",
        side_effect=InvalidURL("Unsupported protocol"),
        base_error="cannot_connect",
    ),
)
async def form_invalid_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
    *,
    side_effect: Exception,
    base_error: str,
) -> None:
    """Test we get the import form."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        respx.get("invalid-url.com").mock(side_effect=side_effect)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: "invalid-url.com",
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": base_error})
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(CALENDAR_NAME)
        expect(result3["data"]).to_equal(
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            }
        )


@test.skip("requires caplog inspection")
async def unsupported_inputs() -> None:
    """Test that an unsupported inputs results in a form error."""


@test.cases(
    test.case("unauthorized", http_status=401, error="cannot_connect"),
    test.case("forbidden", http_status=403, error="forbidden"),
)
async def form_http_status_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
    *,
    http_status: int,
    error: str,
) -> None:
    """Test we http status."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=http_status,
            )
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": error})
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(CALENDAR_NAME)
        expect(result3["data"]).to_equal(
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            }
        )


@test
async def no_valid_calendar(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
) -> None:
    """Test invalid ics content."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text="blabla",
            )
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "invalid_ics_file"})
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: False,
            },
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(CALENDAR_NAME)
        expect(result3["data"]).to_equal(
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: False,
            }
        )


@test
async def duplicate_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test two calendars cannot be added with the same name."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: CALENDAR_NAME,
            CONF_URL: "http://other-calendar.com",
            CONF_VERIFY_SSL: True,
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def duplicate_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test two calendars cannot be added with the same url."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "new name",
            CONF_URL: CALENDER_URL,
            CONF_VERIFY_SSL: True,
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_unauthorized_basic_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
) -> None:
    """Test 401 with WWW-Authenticate: Basic triggers auth step and succeeds."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=401,
                headers={"www-authenticate": 'Basic realm="test"'},
            )
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("auth")

        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(CALENDAR_NAME)
        expect(result3["data"]).to_equal(
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            }
        )


@test
async def form_auth_invalid_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
) -> None:
    """Test wrong credentials in auth step shows invalid_auth error."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=401,
                headers={"www-authenticate": 'Basic realm="test"'},
            )
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("auth")

        # Wrong credentials - server still returns 401
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "wrong",
                CONF_PASSWORD: "wrong",
            },
        )
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["step_id"]).to_equal("auth")
        expect(result3["errors"]).to_equal({"base": "invalid_auth"})

        # Correct credentials
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result4["title"]).to_equal(CALENDAR_NAME)


@test
async def form_auth_forbidden_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test 403 in auth step aborts the flow."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=401,
                headers={"www-authenticate": 'Basic realm="test"'},
            )
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("auth")

        respx.get(CALENDER_URL).mock(return_value=Response(status_code=403))
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("forbidden")


@test
async def form_auth_invalid_ics_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid ICS in auth step aborts the flow."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=401,
                headers={"www-authenticate": 'Basic realm="test"'},
            )
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("auth")

        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text="not valid ics",
            )
        )
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("invalid_ics_file")


@test.cases(
    test.case(
        "timeout",
        side_effect=TimeoutException("Connection timed out"),
        base_error="timeout_connect",
    ),
    test.case(
        "http_error",
        side_effect=HTTPError("Connection failed"),
        base_error="cannot_connect",
    ),
)
async def form_auth_connection_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ics: str = Depends(ics_content),
    *,
    side_effect: Exception,
    base_error: str,
) -> None:
    """Test connection errors in auth step show retryable errors."""
    with respx.mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=401,
                headers={"www-authenticate": 'Basic realm="test"'},
            )
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: CALENDAR_NAME,
                CONF_URL: CALENDER_URL,
                CONF_VERIFY_SSL: True,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("auth")

        # Connection error during auth
        respx.get(CALENDER_URL).mock(side_effect=side_effect)
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["step_id"]).to_equal("auth")
        expect(result3["errors"]).to_equal({"base": base_error})

        # Retry with success
        respx.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=ics,
            )
        )
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pass",
            },
        )
        expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
