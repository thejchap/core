"""Test the Aseko Pool Live config flow."""

from unittest.mock import patch

from aioaseko import AsekoAPIError, AsekoInvalidCredentials, User
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.aseko_pool_live.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.aseko_pool_live._fixtures import user
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def async_step_user_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})


@test
async def async_step_user_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
            return_value=user,
        ),
        patch(
            "homeassistant.components.aseko_pool_live.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "aseko@example.com",
                CONF_PASSWORD: "passw0rd",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("aseko@example.com")
    expect(result2["data"]).to_equal(
        {
            CONF_EMAIL: "aseko@example.com",
            CONF_PASSWORD: "passw0rd",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("cannot_connect", AsekoAPIError, "cannot_connect"),
    test.case("invalid_auth", AsekoInvalidCredentials, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def async_step_user_exception(
    error_web: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
        return_value=user,
        side_effect=error_web,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "aseko@example.com",
                CONF_PASSWORD: "passw0rd",
            },
        )

        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": reason})


@test.cases(
    test.case("cannot_connect", AsekoAPIError, "cannot_connect"),
    test.case("invalid_auth", AsekoInvalidCredentials, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def get_account_info_exceptions(
    error_web: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test we handle config flow exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
        return_value=user,
        side_effect=error_web,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "aseko@example.com",
                CONF_PASSWORD: "passw0rd",
            },
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": reason})


@test
async def async_step_reauth_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test successful reauthentication."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="a_user_id",
        data={CONF_EMAIL: "aseko@example.com", CONF_PASSWORD: "passw0rd"},
        version=2,
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
            return_value=user,
        ),
        patch(
            "homeassistant.components.aseko_pool_live.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "aseko@example.com", CONF_PASSWORD: "new_password"},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(mock_entry.unique_id).to_equal("a_user_id")
    expect(dict(mock_entry.data)).to_equal(
        {
            CONF_EMAIL: "aseko@example.com",
            CONF_PASSWORD: "new_password",
        }
    )


@test
async def async_step_reauth_mismatch(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test mismatch reauthentication."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="UID",
        data={CONF_EMAIL: "aseko@example.com", CONF_PASSWORD: "passw0rd"},
        version=2,
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
            return_value=user,
        ),
        patch(
            "homeassistant.components.aseko_pool_live.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "aseko@example.com", CONF_PASSWORD: "new_password"},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(mock_entry.unique_id).to_equal("UID")
    expect(dict(mock_entry.data)).to_equal(
        {
            CONF_EMAIL: "aseko@example.com",
            CONF_PASSWORD: "passw0rd",
        }
    )


@test.cases(
    test.case("cannot_connect", AsekoAPIError, "cannot_connect"),
    test.case("invalid_auth", AsekoInvalidCredentials, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def async_step_reauth_exception(
    error_web: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    user: User = Depends(user),
) -> None:
    """Test we get the form."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="UID",
        data={CONF_EMAIL: "aseko@example.com"},
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.aseko_pool_live.config_flow.Aseko.login",
        return_value=user,
        side_effect=error_web,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "aseko@example.com",
                CONF_PASSWORD: "passw0rd",
            },
        )

        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": reason})
