"""Test the Verisure config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test
from verisure import Error as VerisureError, LoginError as VerisureLoginError

from homeassistant import config_entries
from homeassistant.components.verisure.const import (
    CONF_GIID,
    CONF_LOCK_CODE_DIGITS,
    DEFAULT_LOCK_CODE_DIGITS,
    DOMAIN,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_verisure_config_flow,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_single_installation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
) -> None:
    """Test a full user initiated configuration flow with a single installation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    verisure.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in verisure.get_installations.return_value.items()
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("ascending (12345th street)")
    expect(result2.get("data")).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_user_flow_multiple_installations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
) -> None:
    """Test a full user initiated configuration flow with multiple installations."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("step_id")).to_equal("installation")
    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_be(None)

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"giid": "54321"}
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("descending (54321th street)")
    expect(result3.get("data")).to_equal(
        {
            CONF_GIID: "54321",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_user_flow_single_installation_with_mfa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
) -> None:
    """Test a full user initiated flow with a single installation and mfa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    verisure.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("mfa")

    verisure.login.side_effect = None
    verisure.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in verisure.get_installations.return_value.items()
    }

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"code": "123456"},
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("ascending (12345th street)")
    expect(result3.get("data")).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(1)
    expect(len(verisure.request_mfa.mock_calls)).to_equal(1)
    expect(len(verisure.validate_mfa.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_user_flow_multiple_installations_with_mfa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
) -> None:
    """Test a full user initiated configuration flow with multiple installations and mfa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    verisure.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("mfa")

    verisure.login.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"code": "123456"},
    )
    await hass.async_block_till_done()

    expect(result3.get("step_id")).to_equal("installation")
    expect(result3.get("type")).to_be(FlowResultType.FORM)
    expect(result3.get("errors")).to_be(None)

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"], {"giid": "54321"}
    )
    await hass.async_block_till_done()

    expect(result4.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result4.get("title")).to_equal("descending (54321th street)")
    expect(result4.get("data")).to_equal(
        {
            CONF_GIID: "54321",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(1)
    expect(len(verisure.request_mfa.mock_calls)).to_equal(1)
    expect(len(verisure.validate_mfa.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=VerisureLoginError, error="invalid_auth"),
    test.case("unknown", side_effect=VerisureError, error="unknown"),
)
async def verisure_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test a flow with an invalid Verisure My Pages login."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    verisure.login.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": error})

    verisure.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )
    verisure.request_mfa.side_effect = side_effect

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    verisure.request_mfa.side_effect = None

    expect(result3.get("type")).to_be(FlowResultType.FORM)
    expect(result3.get("step_id")).to_equal("user")
    expect(result3.get("errors")).to_equal({"base": "unknown_mfa"})

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result4.get("type")).to_be(FlowResultType.FORM)
    expect(result4.get("step_id")).to_equal("mfa")

    verisure.validate_mfa.side_effect = side_effect

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {"code": "123456"},
    )
    expect(result5.get("type")).to_be(FlowResultType.FORM)
    expect(result5.get("step_id")).to_equal("mfa")
    expect(result5.get("errors")).to_equal({"base": error})

    verisure.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in verisure.get_installations.return_value.items()
    }
    verisure.validate_mfa.side_effect = None
    verisure.login.side_effect = None

    result6 = await hass.config_entries.flow.async_configure(
        result5["flow_id"],
        {"code": "654321"},
    )
    await hass.async_block_till_done()

    expect(result6.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result6.get("title")).to_equal("ascending (12345th street)")
    expect(result6.get("data")).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(3)
    expect(len(verisure.request_mfa.mock_calls)).to_equal(2)
    expect(len(verisure.validate_mfa.mock_calls)).to_equal(2)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP discovery works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(
            ip="1.2.3.4", macaddress="0123456789ab", hostname="mock_hostname"
        ),
        context={"source": config_entries.SOURCE_DHCP},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result.get("step_id")).to_equal("reauth_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "correct horse battery staple",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "correct horse battery staple",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_flow_with_mfa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a reauthentication flow with MFA."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result.get("step_id")).to_equal("reauth_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    verisure.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "correct horse battery staple!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("reauth_mfa")

    verisure.login.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {"code": "123456"},
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.ABORT)
    expect(result3.get("reason")).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "correct horse battery staple!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(2)
    expect(len(verisure.request_mfa.mock_calls)).to_equal(1)
    expect(len(verisure.validate_mfa.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=VerisureLoginError, error="invalid_auth"),
    test.case("unknown", side_effect=VerisureError, error="unknown"),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    verisure: MagicMock = Depends(mock_verisure_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test a reauthentication flow with errors."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    verisure.login.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "WrOngP4ssw0rd!",
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("step_id")).to_equal("reauth_confirm")
    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": error})

    verisure.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )
    verisure.request_mfa.side_effect = side_effect

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.FORM)
    expect(result3.get("step_id")).to_equal("reauth_confirm")
    expect(result3.get("errors")).to_equal({"base": "unknown_mfa"})

    verisure.request_mfa.side_effect = None

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    expect(result4.get("type")).to_be(FlowResultType.FORM)
    expect(result4.get("step_id")).to_equal("reauth_mfa")

    verisure.validate_mfa.side_effect = side_effect

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {"code": "123456"},
    )
    expect(result5.get("type")).to_be(FlowResultType.FORM)
    expect(result5.get("step_id")).to_equal("reauth_mfa")
    expect(result5.get("errors")).to_equal({"base": error})

    verisure.validate_mfa.side_effect = None
    verisure.login.side_effect = None
    verisure.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in verisure.get_installations.return_value.items()
    }

    await hass.config_entries.flow.async_configure(
        result5["flow_id"],
        {"code": "654321"},
    )
    await hass.async_block_till_done()

    expect(config_entry.data).to_equal(
        {
            CONF_GIID: "12345",
            CONF_EMAIL: "verisure_my_pages@example.com",
            CONF_PASSWORD: "SuperS3cr3t!",
        }
    )

    expect(len(verisure.login.mock_calls)).to_equal(4)
    expect(len(verisure.request_mfa.mock_calls)).to_equal(2)
    expect(len(verisure.validate_mfa.mock_calls)).to_equal(2)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options config flow."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="12345", data={}, version=2)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.verisure.async_setup_entry",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_LOCK_CODE_DIGITS: 4},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal({CONF_LOCK_CODE_DIGITS: DEFAULT_LOCK_CODE_DIGITS})
