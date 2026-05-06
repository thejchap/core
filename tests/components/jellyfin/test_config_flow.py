"""Test the jellyfin config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
from voluptuous.error import Invalid

from homeassistant import config_entries
from homeassistant.components.jellyfin.const import (
    CONF_AUDIO_CODEC,
    CONF_CLIENT_DEVICE_ID,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import async_load_json_fixture
from ._fixtures import (
    mock_client,
    mock_client_device_id,
    mock_config_entry,
    mock_jellyfin,
    mock_setup_entry,
)
from .const import REAUTH_INPUT, TEST_PASSWORD, TEST_URL, TEST_USERNAME, USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _jellyfin: MagicMock = Depends(mock_jellyfin),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    _device_id: MagicMock = Depends(mock_client_device_id),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the complete configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("JELLYFIN-SERVER")
    expect(result2["data"]).to_equal(
        {
            CONF_CLIENT_DEVICE_ID: "TEST-UUID",
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        }
    )

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)
    expect(len(client.auth.login.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(client.jellyfin.get_user_settings.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    _device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test configuration with an unreachable server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    _device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test configuration with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)
    expect(len(client.auth.login.mock_calls)).to_equal(1)


@test
async def form_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test configuration with an unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    client.auth.connect_to_address.side_effect = Exception("UnknownException")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)


@test
async def form_persists_device_id_on_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test persisting the device id on error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    device_id.return_value = "TEST-UUID-1"
    client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    device_id.return_value = "TEST-UUID-2"
    client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result3).to_be_truthy()
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["data"]).to_equal(
        {
            CONF_CLIENT_DEVICE_ID: "TEST-UUID-1",
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        }
    )


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the case where the user tries to configure an already configured entry."""
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test a reauth flow."""
    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass,
        "auth-connect-address.json",
    )
    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login-failure.json",
    )

    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login.json",
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauth_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test an unreachable server during a reauth flow."""
    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass,
        "auth-connect-address.json",
    )
    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login-failure.json",
    )

    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)

    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login.json",
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test
async def reauth_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test invalid credentials during a reauth flow."""
    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass,
        "auth-connect-address.json",
    )
    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login-failure.json",
    )

    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)
    expect(len(client.auth.login.mock_calls)).to_equal(1)

    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login.json",
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test
async def reauth_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_client),
) -> None:
    """Test an unexpected exception during a reauth flow."""
    client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass,
        "auth-connect-address.json",
    )
    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login-failure.json",
    )

    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    client.auth.connect_to_address.side_effect = Exception("UnknownException")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    expect(len(client.auth.connect_to_address.mock_calls)).to_equal(1)

    client.auth.login.return_value = await async_load_json_fixture(
        hass,
        "auth-login.json",
    )
    client.auth.connect_to_address.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=REAUTH_INPUT,
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    expect(config_entry.options).to_equal({})
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(CONF_AUDIO_CODEC not in config_entry.options).to_be_truthy()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    raised = False
    try:
        await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_AUDIO_CODEC: "ogg"}
        )
    except Invalid:
        raised = True
    expect(raised).to_be_truthy()


@test.cases(
    test.case("aac", codec="aac"),
    test.case("wma", codec="wma"),
    test.case("vorbis", codec="vorbis"),
    test.case("mp3", codec="mp3"),
)
async def setting_codec(
    codec: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _jellyfin: MagicMock = Depends(mock_jellyfin),
) -> None:
    """Test setting the audio_codec."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_AUDIO_CODEC: codec}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options[CONF_AUDIO_CODEC]).to_equal(codec)
