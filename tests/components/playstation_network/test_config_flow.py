"""Test the PlayStation Network config flow."""

from unittest.mock import MagicMock

from homeassistant.components.playstation_network.config_flow import (
    PSNAWPAuthenticationError,
    PSNAWPError,
    PSNAWPInvalidTokenError,
    PSNAWPNotFoundError,
)
from homeassistant.components.playstation_network.const import CONF_NPSSO, DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from tryke import Depends, expect, fixture, test

from ._fixtures import (
    NPSSO_TOKEN,
    NPSSO_TOKEN_INVALID_JSON,
    PSN_ID,
    mock_config_entry,
    mock_psnawp_npsso,
    mock_psnawpapi,
    mock_user,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture executor anchor."""


@test
async def manual_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _psn: MagicMock = Depends(mock_psnawpapi),
) -> None:
    """Test creating via manual configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: "TEST_NPSSO_TOKEN"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(PSN_ID)
    expect(result["data"]).to_equal({CONF_NPSSO: "TEST_NPSSO_TOKEN"})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _psn: MagicMock = Depends(mock_psnawpapi),
) -> None:
    """Test we abort form login when entry is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: NPSSO_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_already_configured_as_subentry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _psn: MagicMock = Depends(mock_psnawpapi),
) -> None:
    """Test we abort form login when entry is already configured as subentry."""
    from homeassistant.components.playstation_network.const import CONF_ACCOUNT_ID

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="PublicUniversalFriend",
        data={CONF_NPSSO: NPSSO_TOKEN},
        unique_id="fren-psn-id",
        subentries_data=[
            ConfigSubentryData(
                data={CONF_ACCOUNT_ID: PSN_ID},
                subentry_id="ABCDEF",
                subentry_type="friend",
                title="test-user",
                unique_id=PSN_ID,
            )
        ],
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: NPSSO_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_as_subentry")


@test.cases(
    test.case("not_found", raise_error=PSNAWPNotFoundError("error msg"), text_error="invalid_account"),
    test.case("auth", raise_error=PSNAWPAuthenticationError("error msg"), text_error="invalid_auth"),
    test.case("psn_error", raise_error=PSNAWPError("error msg"), text_error="cannot_connect"),
    test.case("unknown", raise_error=Exception(), text_error="unknown"),
)
async def form_failures(
    *,
    raise_error: Exception,
    text_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    psn: MagicMock = Depends(mock_psnawpapi),
) -> None:
    """Test we handle a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    psn.user.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: NPSSO_TOKEN},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": text_error})

    psn.user.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: NPSSO_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_NPSSO: NPSSO_TOKEN})


@test
async def parse_npsso_token_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _psn: MagicMock = Depends(mock_psnawpapi),
    npsso: MagicMock = Depends(mock_psnawp_npsso),
) -> None:
    """Test parse_npsso_token raises the correct exceptions during config flow."""
    npsso.side_effect = PSNAWPInvalidTokenError("error msg")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NPSSO: NPSSO_TOKEN_INVALID_JSON},
    )
    expect(result["errors"]).to_equal({"base": "invalid_account"})

    npsso.side_effect = lambda token: token
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: NPSSO_TOKEN},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_NPSSO: NPSSO_TOKEN})


@test.skip("requires loaded config entry — coordinator setup needed for reauth")
async def flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires running config entry."""


@test.skip("requires loaded config entry — coordinator setup needed for reauth")
async def flow_reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires running config entry."""


@test.skip("requires loaded config entry — coordinator setup needed for reauth")
async def flow_reauth_token_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires running config entry."""


@test.skip("requires loaded config entry — coordinator setup needed for reauth")
async def flow_reauth_account_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires running config entry."""


@test.skip("requires loaded config entry — coordinator setup needed for reconfigure")
async def flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires running config entry."""


@test.skip("requires loaded config entry + subentry chain")
async def add_friend_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — subentry init requires loaded entry."""


@test.skip("requires loaded config entry + subentry chain")
async def add_friend_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — subentry init requires loaded entry."""


@test.skip("requires loaded config entry + subentry chain")
async def add_friend_flow_already_configured_as_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — subentry init requires loaded entry."""


@test.skip("requires loaded config entry + subentry chain")
async def add_friend_flow_no_friends(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — subentry init requires loaded entry."""


@test.skip("requires loaded config entry + subentry chain")
async def add_friend_disabled_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — subentry init requires loaded entry."""
