"""Test the jellyfin config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

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
from .const import REAUTH_INPUT, TEST_PASSWORD, TEST_URL, TEST_USERNAME, USER_INPUT
from ._fixtures import (
    mock_client,
    mock_client_device_id,
    mock_config_entry,
    mock_jellyfin,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
    _mock_client_device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test the complete configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
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


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
    _mock_client_device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test configuration with an unreachable server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
    _mock_client_device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test configuration with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test configuration with an unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client.auth.connect_to_address.side_effect = Exception("UnknownException")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_persists_device_id_on_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
    mock_client_device_id: MagicMock = Depends(mock_client_device_id),
) -> None:
    """Test persisting the device id on error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client_device_id.return_value = "TEST-UUID-1"
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    mock_client_device_id.return_value = "TEST-UUID-2"
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

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
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    _mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test the case where the user tries to configure an already configured entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test a reauth flow."""
    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauth_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test an unreachable server during a reauth flow."""
    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test
async def reauth_invalid(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test invalid credentials during a reauth flow."""
    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test
async def reauth_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    mock_client: MagicMock = Depends(mock_client),
) -> None:
    """Test an unexpected exception during a reauth flow."""
    mock_client.auth.connect_to_address.return_value = await async_load_json_fixture(
        hass, "auth-connect-address.json"
    )
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_client.auth.connect_to_address.side_effect = Exception("UnknownException")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )
    mock_client.auth.connect_to_address.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=REAUTH_INPUT
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("aac", codec="aac"),
    test.case("wma", codec="wma"),
    test.case("vorbis", codec="vorbis"),
    test.case("mp3", codec="mp3"),
)
async def setting_codec(
    codec: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_jellyfin: MagicMock = Depends(mock_jellyfin),
    _mock_client: MagicMock = Depends(mock_client),
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
