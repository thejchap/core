"""Test the imap config flow."""

import ssl
from unittest.mock import AsyncMock, patch

from aioimaplib import AioImapException
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.imap.const import (
    CONF_CHARSET,
    CONF_FOLDER,
    CONF_SEARCH,
    DOMAIN,
)
from homeassistant.components.imap.errors import InvalidAuth, InvalidFolder
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_CONFIG = {
    "username": "email@email.com",
    "password": "password",
    "server": "imap.server.com",
    "port": 993,
    "charset": "utf-8",
    "folder": "INBOX",
    "search": "UnSeen UnDeleted",
    "event_message_data": ["text", "headers"],
}

MOCK_OPTIONS = {
    "folder": "INBOX",
    "search": "UnSeen UnDeleted",
    "event_message_data": ["text", "headers"],
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("email@email.com")
    expect(result2["data"]).to_equal(MOCK_CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def entry_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test aborting if the entry is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "email@email.com",
            "password": "password",
            "server": "imap.server.com",
            "port": 993,
            "charset": "utf-8",
            "folder": "INBOX",
            "search": "UnSeen UnDeleted",
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=InvalidAuth,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(
        {
            CONF_USERNAME: "invalid_auth",
            CONF_PASSWORD: "invalid_auth",
        }
    )


@test.cases(
    test.case("timeout", exc=TimeoutError, error="cannot_connect"),
    test.case("aio_imap", exc=AioImapException(""), error="cannot_connect"),
    test.case("ssl", exc=ssl.SSLError, error="ssl_error"),
)
async def form_cannot_connect(
    exc: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=exc,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})

    expect(
        {
            key: key.description.get("suggested_value")
            for key in result2["data_schema"].schema
        }
    ).to_equal(MOCK_CONFIG)


@test
async def form_invalid_charset(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid charset."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "NO",
            [b"The specified charset is not supported"],
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_CHARSET: "invalid_charset"})


@test
async def form_invalid_folder(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid folder selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=InvalidFolder,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_FOLDER: "invalid_folder"})


@test
async def form_invalid_search(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid search."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("BAD", [b"Invalid search"])
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_SEARCH: "invalid_search"})


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            CONF_USERNAME: "email@email.com",
            CONF_NAME: "Mock Title",
        }
    )

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=InvalidAuth,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PASSWORD: "test-wrong-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal(
            {
                CONF_USERNAME: "invalid_auth",
                CONF_PASSWORD: "invalid_auth",
            }
        )


@test
async def reauth_failed_conn_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PASSWORD: "test-wrong-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def options_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show the options form."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    new_config = MOCK_OPTIONS.copy()
    new_config["folder"] = "INBOX.Notifications"
    new_config["search"] = "UnSeen UnDeleted!!INVALID"

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("BAD", [b"Invalid search"])
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], new_config
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_SEARCH: "invalid_search"})

    new_config["search"] = "UnSeen UnDeleted"

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("OK", [b""])
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            new_config,
        )
        await hass.async_block_till_done()
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["data"]).to_equal({})
    for key, value in new_config.items():
        expect(entry.data[key]).to_equal(value)


@test
async def key_options_in_options_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we cannot change options if that would cause duplicates."""
    entry1 = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry1.add_to_hass(hass)
    await hass.config_entries.async_setup(entry1.entry_id)

    config2 = MOCK_CONFIG.copy()
    config2["folder"] = "INBOX.Notifications"
    entry2 = MockConfigEntry(domain=DOMAIN, data=config2)
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)

    result = await hass.config_entries.options.async_init(entry2.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    new_config = MOCK_OPTIONS.copy()

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = ("OK", [b""])
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            new_config,
        )
        await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "already_configured"})


@test.cases(
    test.case(
        "valid_message_size",
        advanced_options={"max_message_size": 8192},
        assert_result=FlowResultType.CREATE_ENTRY,
    ),
    test.case(
        "invalid_message_size_low",
        advanced_options={"max_message_size": 1024},
        assert_result=FlowResultType.FORM,
    ),
    test.case(
        "invalid_message_size_high",
        advanced_options={"max_message_size": 65536},
        assert_result=FlowResultType.FORM,
    ),
    test.case(
        "valid_template",
        advanced_options={"custom_event_data_template": "{{ subject }}"},
        assert_result=FlowResultType.CREATE_ENTRY,
    ),
    test.case(
        "invalid_template",
        advanced_options={"custom_event_data_template": "{{ invalid_syntax"},
        assert_result=FlowResultType.FORM,
    ),
    test.case(
        "enable_push_true",
        advanced_options={"enable_push": True},
        assert_result=FlowResultType.CREATE_ENTRY,
    ),
    test.case(
        "enable_push_false",
        advanced_options={"enable_push": False},
        assert_result=FlowResultType.CREATE_ENTRY,
    ),
)
async def advanced_options_form(
    advanced_options: dict[str, str],
    assert_result: FlowResultType,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show the advanced options."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    result = await hass.config_entries.options.async_init(
        entry.entry_id,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    new_config = MOCK_OPTIONS.copy()
    new_config.update(advanced_options)

    try:
        with patch(
            "homeassistant.components.imap.config_flow.connect_to_server"
        ) as mock_client:
            mock_client.return_value.search.return_value = ("OK", [b""])
            result2 = await hass.config_entries.options.async_configure(
                result["flow_id"], new_config
            )
            expect(result2["type"]).to_equal(assert_result)

            if result2.get("errors") is not None:
                expect(assert_result).to_be(FlowResultType.FORM)
            else:
                for key, value in new_config.items():
                    expect(entry.data[key]).to_equal(value)
    except vol.Invalid:
        expect(assert_result).to_be(FlowResultType.FORM)


@test.cases(
    test.case("python_default_no_verify", cipher_list="python_default", verify_ssl=False),
    test.case("python_default_verify", cipher_list="python_default", verify_ssl=True),
    test.case("modern_no_verify", cipher_list="modern", verify_ssl=False),
    test.case("modern_verify", cipher_list="modern", verify_ssl=True),
    test.case("intermediate_no_verify", cipher_list="intermediate", verify_ssl=False),
    test.case("intermediate_verify", cipher_list="intermediate", verify_ssl=True),
)
async def config_flow_with_cipherlist_and_ssl_verify(
    cipher_list: str,
    verify_ssl: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test with alternate cipherlist or disabled ssl verification."""
    config = MOCK_CONFIG.copy()
    config["ssl_cipher_list"] = cipher_list
    config["verify_ssl"] = verify_ssl
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("email@email.com")
    expect(result2["data"]).to_equal(config)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("empty_event_data", event_message_data=[]),
    test.case("headers_only", event_message_data=["headers"]),
    test.case("text_and_headers", event_message_data=["text", "headers"]),
)
async def config_flow_with_event_message_data(
    event_message_data: list,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test with different message data."""
    config = MOCK_CONFIG.copy()
    config["event_message_data"] = event_message_data
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": False},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("email@email.com")
    expect(result2["data"]).to_equal(config)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_from_with_advanced_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test if advanced settings show correctly."""
    config = MOCK_CONFIG.copy()
    config["ssl_cipher_list"] = "python_default"
    config["verify_ssl"] = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("cannot_connect")
    expect("ssl_cipher_list" in result2["data_schema"].schema).to_be(True)

    config["ssl_cipher_list"] = "modern"
    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], config
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("email@email.com")
    expect(result3["data"]).to_equal(config)
    expect(len(setup_entry.mock_calls)).to_equal(1)
