"""Test the ista EcoTrend config flow."""

from unittest.mock import AsyncMock, MagicMock

from pyecotrend_ista import LoginError, ServerError
from tryke import Depends, expect, fixture, test

from homeassistant.components.ista_ecotrend.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import ista_config_entry, mock_ista, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _ista: MagicMock = Depends(mock_ista),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Max Istamann")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=LoginError(None), error_text="invalid_auth"),
    test.case("cannot_connect", side_effect=ServerError, error_text="cannot_connect"),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def form_error_and_recover(
    side_effect: Exception,
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
    ista: MagicMock = Depends(mock_ista),
) -> None:
    """Test config flow error and recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    ista.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    ista.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Max Istamann")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(ista_config_entry),
) -> None:
    """Test reauth flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=LoginError(None), error_text="invalid_auth"),
    test.case("cannot_connect", side_effect=ServerError, error_text="cannot_connect"),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def reauth_error_and_recover(
    side_effect: Exception,
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(ista_config_entry),
    ista: MagicMock = Depends(mock_ista),
) -> None:
    """Test reauth flow error and recover."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    ista.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    ista.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(ista_config_entry),
) -> None:
    """Test we abort form login when entry is already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_reauth_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow unique id mismatch."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
        unique_id="42243134-21f6-40a2-a79f-e417a3a12104",
    )

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(ista_config_entry),
) -> None:
    """Test reconfigure flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=LoginError(None), error_text="invalid_auth"),
    test.case("cannot_connect", side_effect=ServerError, error_text="cannot_connect"),
    test.case("unknown", side_effect=IndexError, error_text="unknown"),
)
async def reconfigure_error_and_recover(
    side_effect: Exception,
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(ista_config_entry),
    ista: MagicMock = Depends(mock_ista),
) -> None:
    """Test reconfigure flow error and recover."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    ista.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    ista.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow unique id mismatch."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
        unique_id="42243134-21f6-40a2-a79f-e417a3a12104",
    )

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
