"""Test the ntfy config flow."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiontfy import AccountTokenResponse
from aiontfy.exceptions import (
    NtfyException,
    NtfyHTTPError,
    NtfyUnauthorizedAuthenticationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ntfy.const import (
    CONF_MESSAGE,
    CONF_PRIORITY,
    CONF_TAGS,
    CONF_TITLE,
    CONF_TOPIC,
    DOMAIN,
    SECTION_AUTH,
    SECTION_FILTER,
)
from homeassistant.config_entries import SOURCE_USER, ConfigSubentry
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ntfy._fixtures import (
    config_entry,
    mock_aiontfy,
    mock_async_zeroconf,
    mock_random,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf),
    _random: MagicMock = Depends(mock_random),
) -> None:
    """Wire mock_network + mock_async_zeroconf + mock_random (autouse) for every test."""


@test.cases(
    test.case(
        "with_auth",
        {
            CONF_URL: "https://ntfy.sh",
            CONF_VERIFY_SSL: True,
            SECTION_AUTH: {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        },
        {
            CONF_URL: "https://ntfy.sh/",
            CONF_VERIFY_SSL: True,
            CONF_USERNAME: "username",
            CONF_TOKEN: "token",
        },
    ),
    test.case(
        "no_auth",
        {CONF_URL: "https://ntfy.sh", CONF_VERIFY_SSL: True, SECTION_AUTH: {}},
        {
            CONF_URL: "https://ntfy.sh/",
            CONF_VERIFY_SSL: True,
            CONF_USERNAME: None,
            CONF_TOKEN: "token",
        },
    ),
)
async def form(
    user_input: dict[str, Any],
    entry_data: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ntfy.sh")
    expect(result["data"]).to_equal(entry_data)
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "http_error",
        NtfyHTTPError(418001, 418, "I'm a teapot", ""),
        "cannot_connect",
    ),
    test.case(
        "unauthorized",
        NtfyUnauthorizedAuthenticationError(
            40101,
            401,
            "unauthorized",
            "https://ntfy.sh/docs/publish/#authentication",
        ),
        "invalid_auth",
    ),
    test.case("generic", NtfyException, "cannot_connect"),
    test.case("type_error", TypeError, "unknown"),
)
async def form_errors(
    exception: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    mock_aiontfy_: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    mock_aiontfy_.account.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://ntfy.sh",
            CONF_VERIFY_SSL: True,
            SECTION_AUTH: {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_aiontfy_.account.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://ntfy.sh",
            CONF_VERIFY_SSL: True,
            SECTION_AUTH: {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ntfy.sh")
    expect(result["data"]).to_equal(
        {
            CONF_URL: "https://ntfy.sh/",
            CONF_VERIFY_SSL: True,
            CONF_USERNAME: "username",
            CONF_TOKEN: "token",
        }
    )
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_: MockConfigEntry = Depends(config_entry),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test we abort when entry is already configured."""
    config_entry_.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "https://ntfy.sh",
            CONF_VERIFY_SSL: True,
            SECTION_AUTH: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def add_topic_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test add topic subentry flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://ntfy.sh/", CONF_VERIFY_SSL: True, CONF_USERNAME: None},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "topic"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("add_topic" in result["menu_options"]).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "add_topic"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_topic")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "mytopic",
            SECTION_FILTER: {
                CONF_PRIORITY: ["5"],
                CONF_TAGS: ["octopus", "+1"],
                CONF_TITLE: "title",
                CONF_MESSAGE: "triggered",
            },
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    subentry_id = next(iter(entry.subentries))
    expect(entry.subentries).to_equal(
        {
            subentry_id: ConfigSubentry(
                data={
                    CONF_TOPIC: "mytopic",
                    CONF_PRIORITY: ["5"],
                    CONF_TAGS: ["octopus", "+1"],
                    CONF_TITLE: "title",
                    CONF_MESSAGE: "triggered",
                },
                subentry_id=subentry_id,
                subentry_type="topic",
                title="mytopic",
                unique_id="mytopic",
            )
        }
    )

    await hass.async_block_till_done()


@test
async def generated_topic(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_random_: MagicMock = Depends(mock_random),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test add topic subentry flow with generated topic name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://ntfy.sh/", CONF_VERIFY_SSL: True},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "topic"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("generate_topic" in result["menu_options"]).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "generate_topic"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_topic")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "",
            SECTION_FILTER: {},
        },
    )

    mock_random_.assert_called_once()

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "randomtopic",
            CONF_NAME: "mytopic",
            SECTION_FILTER: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    subentry_id = next(iter(entry.subentries))
    expect(entry.subentries).to_equal(
        {
            subentry_id: ConfigSubentry(
                data={CONF_TOPIC: "randomtopic"},
                subentry_id=subentry_id,
                subentry_type="topic",
                title="mytopic",
                unique_id="randomtopic",
            )
        }
    )


@test
async def invalid_topic(
    hass: HomeAssistant = Depends(hass_fixture),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test add topic subentry flow with invalid topic name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://ntfy.sh/", CONF_VERIFY_SSL: True},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "topic"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("add_topic" in result["menu_options"]).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "add_topic"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_topic")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "invalid,topic",
            SECTION_FILTER: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_topic"})

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "mytopic",
            SECTION_FILTER: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    subentry_id = next(iter(entry.subentries))
    expect(entry.subentries).to_equal(
        {
            subentry_id: ConfigSubentry(
                data={CONF_TOPIC: "mytopic"},
                subentry_id=subentry_id,
                subentry_type="topic",
                title="mytopic",
                unique_id="mytopic",
            )
        }
    )


@test
async def topic_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_: MockConfigEntry = Depends(config_entry),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test we abort when entry is already configured."""
    config_entry_.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry_.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (config_entry_.entry_id, "topic"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect("add_topic" in result["menu_options"]).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "add_topic"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_topic")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOPIC: "mytopic",
            SECTION_FILTER: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("password", {CONF_PASSWORD: "password"}),
    test.case("token", {CONF_TOKEN: "newtoken"}),
)
async def flow_reauth(
    user_input: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiontfy_: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reauth flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "username",
            CONF_TOKEN: "token",
        },
    )
    mock_aiontfy_.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_TOKEN]).to_equal("newtoken")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "http_error",
        NtfyHTTPError(418001, 418, "I'm a teapot", ""),
        "cannot_connect",
    ),
    test.case(
        "unauthorized",
        NtfyUnauthorizedAuthenticationError(
            40101,
            401,
            "unauthorized",
            "https://ntfy.sh/docs/publish/#authentication",
        ),
        "invalid_auth",
    ),
    test.case("generic", NtfyException, "cannot_connect"),
    test.case("type_error", TypeError, "unknown"),
)
async def form_reauth_errors(
    exception: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiontfy_: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reauth flow errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "username",
            CONF_TOKEN: "token",
        },
    )
    mock_aiontfy_.account.side_effect = exception
    mock_aiontfy_.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_aiontfy_.account.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "username",
            CONF_TOKEN: "newtoken",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reauth_account_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_: MockConfigEntry = Depends(config_entry),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reauth flow."""
    config_entry_.add_to_hass(hass)
    result = await config_entry_.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "newtoken"},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("account_mismatch")


@test.cases(
    test.case(
        "unset_to_pwd",
        {CONF_USERNAME: None, CONF_TOKEN: None},
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        "reconfigure",
    ),
    test.case(
        "set_to_token",
        {CONF_USERNAME: "username", CONF_TOKEN: "oldtoken"},
        {CONF_TOKEN: "newtoken"},
        "reconfigure_user",
    ),
)
async def flow_reconfigure(
    entry_data: dict[str, str | None],
    user_input: dict[str, str],
    step_id: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiontfy_: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            **entry_data,
        },
    )
    mock_aiontfy_.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("username")
    expect(entry.data[CONF_TOKEN]).to_equal("newtoken")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("unset", {CONF_USERNAME: None, CONF_TOKEN: None}, "reconfigure"),
    test.case(
        "with_user",
        {CONF_USERNAME: "username", CONF_TOKEN: "oldtoken"},
        "reconfigure_user",
    ),
)
async def flow_reconfigure_token(
    entry_data: dict[str, Any],
    step_id: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reconfigure flow with access token."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            **entry_data,
        },
    )

    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(step_id)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "access_token"},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("username")
    expect(entry.data[CONF_TOKEN]).to_equal("access_token"),

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "http_error",
        NtfyHTTPError(418001, 418, "I'm a teapot", ""),
        "cannot_connect",
    ),
    test.case(
        "unauthorized",
        NtfyUnauthorizedAuthenticationError(
            40101,
            401,
            "unauthorized",
            "https://ntfy.sh/docs/publish/#authentication",
        ),
        "invalid_auth",
    ),
    test.case("generic", NtfyException, "cannot_connect"),
    test.case("type_error", TypeError, "unknown"),
)
async def flow_reconfigure_errors(
    exception: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiontfy_: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reconfigure flow errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: None,
            CONF_TOKEN: None,
        },
    )
    mock_aiontfy_.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    mock_aiontfy_.account.side_effect = exception

    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_aiontfy_.account.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("username")
    expect(entry.data[CONF_TOKEN]).to_equal("newtoken")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reconfigure_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_: MockConfigEntry = Depends(config_entry),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reconfigure flow already configured."""
    other_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "username",
        },
    )
    other_config_entry.add_to_hass(hass)

    config_entry_.add_to_hass(hass)
    result = await config_entry_.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(len(hass.config_entries.async_entries())).to_equal(2)


@test
async def flow_reconfigure_account_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test reconfigure flow account mismatch."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "wrong_username",
            CONF_TOKEN: "oldtoken",
        },
    )
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "newtoken"},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("account_mismatch")


@test
async def topic_reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _aiontfy: AsyncMock = Depends(mock_aiontfy),
) -> None:
    """Test topic subentry reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://ntfy.sh/", CONF_USERNAME: None},
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={
                    CONF_TOPIC: "mytopic",
                    CONF_PRIORITY: ["1"],
                    CONF_TAGS: ["owl", "-1"],
                    CONF_TITLE: "",
                    CONF_MESSAGE: "triggered",
                },
                subentry_id="subentry_id",
                subentry_type="topic",
                title="mytopic",
                unique_id="mytopic",
            )
        ],
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await entry.start_subentry_reconfigure_flow(hass, "subentry_id")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_PRIORITY: ["5"],
            CONF_TAGS: ["octopus", "+1"],
            CONF_TITLE: "title",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(entry.subentries).to_equal(
        {
            "subentry_id": ConfigSubentry(
                data={
                    CONF_TOPIC: "mytopic",
                    CONF_PRIORITY: ["5"],
                    CONF_TAGS: ["octopus", "+1"],
                    CONF_TITLE: "title",
                    CONF_MESSAGE: None,
                },
                subentry_id="subentry_id",
                subentry_type="topic",
                title="mytopic",
                unique_id="mytopic",
            )
        }
    )

    await hass.async_block_till_done()
