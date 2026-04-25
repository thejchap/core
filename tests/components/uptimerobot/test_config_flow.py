"""Test the UptimeRobot config flow."""

from unittest.mock import patch

from pyuptimerobot import (
    API_PATH_USER_ME,
    UptimeRobotAuthenticationException,
    UptimeRobotConnectionException,
    UptimeRobotException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.uptimerobot.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import (
    MOCK_UPTIMEROBOT_ACCOUNT,
    MOCK_UPTIMEROBOT_API_KEY,
    MOCK_UPTIMEROBOT_API_KEY_READ_ONLY,
    MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA,
    MOCK_UPTIMEROBOT_EMAIL,
    mock_uptimerobot_api_response,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME, data=MOCK_UPTIMEROBOT_ACCOUNT
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    expect(result2["result"].unique_id).to_equal(MOCK_UPTIMEROBOT_EMAIL)
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(MOCK_UPTIMEROBOT_ACCOUNT["email"])
    expect(result2["data"]).to_equal({CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_key_read_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with read only key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
        return_value=mock_uptimerobot_api_response(
            api_path=API_PATH_USER_ME,
            data=MOCK_UPTIMEROBOT_ACCOUNT,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY_READ_ONLY},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal("not_main_key")


@test.cases(
    test.case("unknown", exception=Exception, error_key="unknown"),
    test.case(
        "cannot_connect", exception=UptimeRobotException, error_key="cannot_connect"
    ),
    test.case(
        "invalid_api_key",
        exception=UptimeRobotAuthenticationException,
        error_key="invalid_api_key",
    ),
)
async def exception_thrown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exception: type[Exception],
    error_key: str,
) -> None:
    """Test user flow throwing exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal(error_key)


@test
async def api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected API error is caught."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
        side_effect=UptimeRobotConnectionException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )

    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def user_unique_id_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating an entry where the unique_id already exists."""
    entry = MockConfigEntry(**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME,
                data=MOCK_UPTIMEROBOT_ACCOUNT,
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "12345"},
        )
        await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test UptimeRobot reauthentication."""
    old_entry = MockConfigEntry(**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA)
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME,
                data=MOCK_UPTIMEROBOT_ACCOUNT,
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauthentication_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test UptimeRobot reauthentication failure."""
    old_entry = MockConfigEntry(**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA)
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            side_effect=UptimeRobotException,
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def reauthentication_failure_no_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test UptimeRobot reauthentication with no existing entry."""
    old_entry = MockConfigEntry(
        **{**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA, "unique_id": None}
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME,
                data=MOCK_UPTIMEROBOT_ACCOUNT,
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_failed_existing")


@test
async def reauthentication_failure_account_not_matching(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test UptimeRobot reauthentication failure when using another account."""
    old_entry = MockConfigEntry(**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA)
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME,
                data={
                    "email": "wrong_account",
                    "monitorsCount": 1,
                },
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal("reauth_failed_matching_account")


@test
async def reconfigure_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the entry can be reconfigured."""
    config_entry = MockConfigEntry(
        **{**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA, "unique_id": None}
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reconfigure")

    new_key = "u0242ac120003-new"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME, data=MOCK_UPTIMEROBOT_ACCOUNT
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: new_key},
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal(new_key)


@test
async def reconfigure_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the entry reconfigure fails with a wrong key."""
    config_entry = MockConfigEntry(
        **{**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA, "unique_id": None}
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("reconfigure")

    wrong_key = "u0242ac120003-wrong"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            side_effect=UptimeRobotAuthenticationException,
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: wrong_key},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(bool(result2["errors"])).to_be(True)
    expect(result2["errors"]["base"]).to_equal("invalid_api_key")

    new_key = "u0242ac120003-new"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME, data=MOCK_UPTIMEROBOT_ACCOUNT
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={CONF_API_KEY: new_key},
        )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal(new_key)
