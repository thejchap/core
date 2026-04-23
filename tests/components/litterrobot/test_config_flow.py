"""Test the Litter-Robot config flow."""

from unittest.mock import MagicMock, PropertyMock, patch

from pylitterbot import Account
from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import mock_account
from .common import ACCOUNT_USER_ID, CONFIG, DOMAIN

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_DISCOVERY_LR4 = DhcpServiceInfo(
    ip="192.168.1.100",
    macaddress="aabbccddeeff",
    hostname="litter-robot4",
)
DHCP_DISCOVERY_LR5 = DhcpServiceInfo(
    ip="192.168.1.101",
    macaddress="aabbccddeef0",
    hostname="whiskerrobots",
)


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_account: MagicMock = Depends(mock_account),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONFIG[DOMAIN][CONF_USERNAME])
    expect(result["data"]).to_equal(CONFIG[DOMAIN])
    expect(result["result"].unique_id).to_equal(ACCOUNT_USER_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test already configured account is rejected before authentication."""
    MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=CONFIG[DOMAIN],
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("unknown", Exception, {"base": "unknown"}),
    test.case("invalid_auth", LitterRobotLoginException, {"base": "invalid_auth"}),
    test.case("cannot_connect", LitterRobotException, {"base": "cannot_connect"}),
)
async def create_entry(
    side_effect: type[Exception],
    connect_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_account: MagicMock = Depends(mock_account),
) -> None:
    """Test creating an entry after error recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.litterrobot.config_flow.Account.connect",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(connect_errors)

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONFIG[DOMAIN][CONF_USERNAME])
    expect(result["data"]).to_equal(CONFIG[DOMAIN])
    expect(result["result"].unique_id).to_equal(ACCOUNT_USER_ID)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_account: Account = Depends(mock_account),
) -> None:
    """Test reauth flow (with fail and recover)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.litterrobot.config_flow.Account.connect",
        side_effect=LitterRobotLoginException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: CONFIG[DOMAIN][CONF_PASSWORD]},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: CONFIG[DOMAIN][CONF_PASSWORD]},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(entry.unique_id).to_equal(ACCOUNT_USER_ID)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_wrong_account(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth flow aborts when credentials belong to a different account."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value="different_user_id",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: CONFIG[DOMAIN][CONF_PASSWORD]},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(entry.unique_id).to_equal(ACCOUNT_USER_ID)
    expect(entry.data).to_equal(CONFIG[DOMAIN])


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_account: Account = Depends(mock_account),
) -> None:
    """Test reconfiguration flow (with fail and recover)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    )
    entry.add_to_hass(hass)

    original_password = entry.data[CONF_PASSWORD]
    new_password = f"{original_password}_new"

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.litterrobot.config_flow.Account.connect",
        side_effect=LitterRobotLoginException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "invalid_auth"})
        expect(entry.data[CONF_PASSWORD]).to_equal(original_password)

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reconfigure_successful")
        expect(entry.unique_id).to_equal(ACCOUNT_USER_ID)
        expect(entry.data[CONF_PASSWORD]).to_equal(new_password)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_discovery_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery aborts when already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG[DOMAIN],
        unique_id=ACCOUNT_USER_ID,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DHCP_DISCOVERY_LR4,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery_full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_account: Account = Depends(mock_account),
) -> None:
    """Test DHCP discovery through to successful entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DHCP_DISCOVERY_LR4,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONFIG[DOMAIN][CONF_USERNAME])
    expect(result["data"]).to_equal(CONFIG[DOMAIN])
    expect(result["result"].unique_id).to_equal(ACCOUNT_USER_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
