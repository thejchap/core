"""Test the Bring! config flow."""

from unittest.mock import AsyncMock, MagicMock

from bring_api import BringAuthException, BringParseException, BringRequestException
from tryke import Depends, expect, fixture, test

from homeassistant.components.bring.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.bring._fixtures import (
    EMAIL,
    PASSWORD,
    bring_config_entry,
    mock_bring_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network

MOCK_DATA_STEP = {
    CONF_EMAIL: EMAIL,
    CONF_PASSWORD: PASSWORD,
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_STEP,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Bring")
    expect(result["data"]).to_equal(MOCK_DATA_STEP)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("cannot_connect", BringRequestException, "cannot_connect"),
    test.case("invalid_auth", BringAuthException, "invalid_auth"),
    test.case("parse_error", BringParseException, "unknown"),
    test.case("index_error", IndexError, "unknown"),
)
async def flow_user_init_data_unknown_error_and_recover(
    raise_error_cls: type[Exception],
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test unknown errors."""
    mock_bring_client.login.side_effect = raise_error_cls()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_STEP,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]["base"]).to_equal(text_error)

    mock_bring_client.login.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_STEP,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["result"].title).to_equal("Bring")
    expect(result["data"]).to_equal(MOCK_DATA_STEP)


@test
async def flow_user_init_data_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort user data set when entry is already configured."""
    bring_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_STEP,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reauth flow."""
    bring_config_entry.add_to_hass(hass)

    result = await bring_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(bring_config_entry.data).to_equal(
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"}
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("cannot_connect", BringRequestException, "cannot_connect"),
    test.case("invalid_auth", BringAuthException, "invalid_auth"),
    test.case("parse_error", BringParseException, "unknown"),
    test.case("index_error", IndexError, "unknown"),
)
async def flow_reauth_error_and_recover(
    raise_error_cls: type[Exception],
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reauth flow."""
    bring_config_entry.add_to_hass(hass)

    result = await bring_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_bring_client.login.side_effect = raise_error_cls()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": text_error})

    mock_bring_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reauth_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort reauth if unique id mismatch."""
    mock_bring_client.uuid = "11111111-11111111-11111111-11111111"

    bring_config_entry.add_to_hass(hass)

    result = await bring_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test
async def flow_reconfigure(
    hass: HomeAssistant = Depends(hass),
    _mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reconfigure flow."""
    bring_config_entry.add_to_hass(hass)
    result = await bring_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(bring_config_entry.data[CONF_EMAIL]).to_equal("new-email")
    expect(bring_config_entry.data[CONF_PASSWORD]).to_equal("new-password")
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("cannot_connect", BringRequestException, "cannot_connect"),
    test.case("invalid_auth", BringAuthException, "invalid_auth"),
    test.case("parse_error", BringParseException, "unknown"),
    test.case("index_error", IndexError, "unknown"),
)
async def flow_reconfigure_errors(
    raise_error_cls: type[Exception],
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reconfigure flow errors."""
    bring_config_entry.add_to_hass(hass)
    result = await bring_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_bring_client.login.side_effect = raise_error_cls()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": text_error})

    mock_bring_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(bring_config_entry.data[CONF_EMAIL]).to_equal("new-email")
    expect(bring_config_entry.data[CONF_PASSWORD]).to_equal("new-password")
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reconfigure_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass),
    bring_config_entry: MockConfigEntry = Depends(bring_config_entry),
    mock_bring_client: AsyncMock = Depends(mock_bring_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort reconfigure if unique id mismatch."""
    mock_bring_client.uuid = "11111111-11111111-11111111-11111111"

    bring_config_entry.add_to_hass(hass)

    result = await bring_config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")
