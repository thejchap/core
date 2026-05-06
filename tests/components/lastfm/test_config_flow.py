"""Test Lastfm config flow."""

from unittest.mock import patch

from pylast import WSError
from tryke import Depends, expect, fixture, test

from homeassistant.components.lastfm.const import (
    CONF_MAIN_USER,
    CONF_USERS,
    DEFAULT_NAME,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    API_KEY,
    CONF_DATA,
    CONF_FRIENDS_DATA,
    CONF_USER_DATA,
    USERNAME_1,
    MockUser,
    patch_setup_entry,
)
from ._fixtures import (
    ComponentSetup,
    config_entry,
    default_user,
    default_user_no_friends,
    imported_config_entry,
    setup_integration,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    user: MockUser = Depends(default_user),
) -> None:
    """Test the full user configuration flow."""
    with patch("pylast.User", return_value=user), patch_setup_entry():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_USER_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(not result["errors"]).to_be_truthy()
        expect(result["step_id"]).to_equal("friends")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_FRIENDS_DATA
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(DEFAULT_NAME)
        expect(result["options"]).to_equal(CONF_DATA)


@test.cases(
    test.case(
        "invalid_auth",
        error=WSError(
            "network",
            "status",
            "Invalid API key - You must be granted a valid key by last.fm",
        ),
        message="invalid_auth",
    ),
    test.case(
        "invalid_account",
        error=WSError("network", "status", "User not found"),
        message="invalid_account",
    ),
    test.case("unknown", error=Exception(), message="unknown"),
    test.case(
        "unknown_strange",
        error=WSError("network", "status", "Something strange"),
        message="unknown",
    ),
)
async def flow_fails(
    error: Exception,
    message: str,
    hass: HomeAssistant = Depends(hass_fixture),
    user: MockUser = Depends(default_user),
) -> None:
    """Test user initialized flow with invalid username."""
    with patch("pylast.User", return_value=MockUser(thrown_error=error)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_USER_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal(message)

    with patch("pylast.User", return_value=user), patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_USER_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(not result["errors"]).to_be_truthy()
        expect(result["step_id"]).to_equal("friends")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_FRIENDS_DATA
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(DEFAULT_NAME)
        expect(result["options"]).to_equal(CONF_DATA)


@test
async def flow_friends_invalid_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    user: MockUser = Depends(default_user),
) -> None:
    """Test user initialized flow with invalid friend username."""
    with patch("pylast.User", return_value=user), patch_setup_entry():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_USER_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("friends")

    with patch(
        "pylast.User",
        return_value=MockUser(
            thrown_error=WSError("network", "status", "User not found")
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_FRIENDS_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("friends")
        expect(result["errors"]["base"]).to_equal("invalid_account")

    with patch("pylast.User", return_value=user), patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_FRIENDS_DATA
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(DEFAULT_NAME)
        expect(result["options"]).to_equal(CONF_DATA)


@test
async def flow_friends_no_friends(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    user: MockUser = Depends(default_user_no_friends),
) -> None:
    """Test options is empty when user has no friends."""
    with (
        patch("pylast.User", return_value=user),
        patch_setup_entry(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_USER_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("friends")
        expect(
            len(result["data_schema"].schema[CONF_USERS].config["options"])
        ).to_equal(0)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
    entry: MockConfigEntry = Depends(config_entry),
    user: MockUser = Depends(default_user),
) -> None:
    """Test updating options."""
    await setup(entry, user)
    with patch("pylast.User", return_value=user):
        cur = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(cur.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_USERS: [USERNAME_1]},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: API_KEY,
            CONF_MAIN_USER: USERNAME_1,
            CONF_USERS: [USERNAME_1],
        }
    )


@test
async def options_flow_incorrect_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
    entry: MockConfigEntry = Depends(config_entry),
    user: MockUser = Depends(default_user),
) -> None:
    """Test updating options doesn't work with incorrect username."""
    await setup(entry, user)
    with patch("pylast.User", return_value=user):
        cur = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(cur.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

    with patch(
        "pylast.User",
        return_value=MockUser(
            thrown_error=WSError("network", "status", "User not found")
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_USERS: [USERNAME_1]},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")
        expect(result["errors"]["base"]).to_equal("invalid_account")

    with patch("pylast.User", return_value=user):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_USERS: [USERNAME_1]},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: API_KEY,
            CONF_MAIN_USER: USERNAME_1,
            CONF_USERS: [USERNAME_1],
        }
    )


@test
async def options_flow_from_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
    entry: MockConfigEntry = Depends(imported_config_entry),
    user: MockUser = Depends(default_user_no_friends),
) -> None:
    """Test updating options gained from import."""
    await setup(entry, user)
    with patch("pylast.User", return_value=user):
        cur = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(cur.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")
        expect(
            len(result["data_schema"].schema[CONF_USERS].config["options"])
        ).to_equal(0)


@test
async def options_flow_without_friends(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
    entry: MockConfigEntry = Depends(config_entry),
    user: MockUser = Depends(default_user_no_friends),
) -> None:
    """Test updating options for someone without friends."""
    await setup(entry, user)
    with patch("pylast.User", return_value=user):
        cur = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(cur.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")
        expect(
            len(result["data_schema"].schema[CONF_USERS].config["options"])
        ).to_equal(0)
