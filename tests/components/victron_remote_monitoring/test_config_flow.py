"""Test the Victron VRM Solar Forecast config flow."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from victron_vrm.exceptions import AuthenticationError, VictronVRMError

from homeassistant.components.victron_remote_monitoring.config_flow import SiteNotFound
from homeassistant.components.victron_remote_monitoring.const import (
    CONF_API_TOKEN,
    CONF_SITE_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_vrm_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _make_site(site_id: int, name: str = "ESS System") -> Mock:
    """Return a mock site object exposing id and name attributes."""
    site = Mock()
    site.id = site_id
    site.name = name
    return site


@test
async def full_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """Test the 2-step flow: token -> select site -> create entry."""
    site1 = _make_site(123456, "ESS")
    site2 = _make_site(987654, "Cabin")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    vrm_client.users.list_sites = AsyncMock(return_value=[site2, site1])
    vrm_client.users.get_site = AsyncMock(return_value=site1)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "test_token"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select_site")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SITE_ID: str(site1.id)}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"VRM for {site1.name}")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: "test_token",
            CONF_SITE_ID: site1.id,
        }
    )
    expect(setup_entry.call_count).to_equal(1)


@test
async def user_step_no_sites(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """No sites available keeps user step with no_sites error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    vrm_client.users.list_sites.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_sites"})

    site = _make_site(999999, "Only Site")
    vrm_client.users.list_sites.return_value = [site]
    vrm_client.users.list_sites.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal({CONF_API_TOKEN: "token", CONF_SITE_ID: site.id})


@test.cases(
    test.case(
        "auth_error",
        side_effect=AuthenticationError("bad", status_code=401),
        expected_error="invalid_auth",
    ),
    test.case(
        "vrm_auth_error",
        side_effect=VictronVRMError("auth", status_code=401, response_data={}),
        expected_error="invalid_auth",
    ),
    test.case(
        "server_error",
        side_effect=VictronVRMError("server", status_code=500, response_data={}),
        expected_error="cannot_connect",
    ),
    test.case(
        "value_error",
        side_effect=ValueError("boom"),
        expected_error="unknown",
    ),
)
async def user_step_errors_then_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test token validation errors (user step) and eventual success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    vrm_client.users.list_sites.side_effect = side_effect
    result_err = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_API_TOKEN: "token"}
    )
    expect(result_err["type"]).to_be(FlowResultType.FORM)
    expect(result_err["step_id"]).to_equal("user")
    expect(result_err["errors"]).to_equal({"base": expected_error})

    site = _make_site(24680, "AutoSite")
    vrm_client.users.list_sites.side_effect = None
    vrm_client.users.list_sites.return_value = [site]
    result_ok = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_API_TOKEN: "token"}
    )
    expect(result_ok["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result_ok["data"]).to_equal(
        {
            CONF_API_TOKEN: "token",
            CONF_SITE_ID: site.id,
        }
    )


@test.cases(
    test.case(
        "auth_403",
        side_effect=AuthenticationError("ExpiredToken", status_code=403),
        return_value=None,
        expected_error="invalid_auth",
    ),
    test.case(
        "vrm_403",
        side_effect=VictronVRMError("forbidden", status_code=403, response_data={}),
        return_value=None,
        expected_error="invalid_auth",
    ),
    test.case(
        "server_500",
        side_effect=VictronVRMError("Internal server error", status_code=500, response_data={}),
        return_value=None,
        expected_error="cannot_connect",
    ),
    test.case(
        "site_not_found",
        side_effect=None,
        return_value=None,
        expected_error="site_not_found",
    ),
    test.case(
        "value_error",
        side_effect=ValueError("missing"),
        return_value=None,
        expected_error="unknown",
    ),
)
async def select_site_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
    *,
    side_effect: Exception | None,
    return_value: Mock | None,
    expected_error: str,
) -> None:
    """Parametrized select_site error scenarios."""
    sites = [_make_site(1, "A"), _make_site(2, "B")]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    vrm_client.users.list_sites = AsyncMock(return_value=sites)
    if side_effect is not None:
        vrm_client.users.get_site = AsyncMock(side_effect=side_effect)
    else:
        vrm_client.users.get_site = AsyncMock(return_value=return_value)
    res_intermediate = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_API_TOKEN: "token"}
    )
    expect(res_intermediate["step_id"]).to_equal("select_site")
    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_SITE_ID: str(sites[0].id)}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select_site")
    expect(result["errors"]).to_equal({"base": expected_error})

    good_site = _make_site(sites[0].id, sites[0].name)
    vrm_client.users.get_site = AsyncMock(return_value=good_site)
    result_success = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_SITE_ID: str(sites[0].id)}
    )
    expect(result_success["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result_success["data"]).to_equal(
        {
            CONF_API_TOKEN: "token",
            CONF_SITE_ID: good_site.id,
        }
    )


@test
async def select_site_duplicate_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """Selecting an already configured site aborts during the select step (multi-site)."""
    site_id = 555
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "token", CONF_SITE_ID: site_id},
        unique_id=str(site_id),
        title="Existing",
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    vrm_client.users.list_sites = AsyncMock(
        return_value=[_make_site(site_id, "Dup"), _make_site(777, "Other")]
    )
    vrm_client.users.get_site = AsyncMock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token2"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select_site")

    res_abort = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SITE_ID: str(site_id)}
    )
    expect(res_abort["type"]).to_be(FlowResultType.ABORT)
    expect(res_abort["reason"]).to_equal("already_configured")
    expect(vrm_client.users.get_site.call_count).to_equal(0)

    result_new = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    other_site = _make_site(777, "Other")
    vrm_client.users.list_sites = AsyncMock(return_value=[other_site])
    result_new2 = await hass.config_entries.flow.async_configure(
        result_new["flow_id"], {CONF_API_TOKEN: "token3"}
    )
    expect(result_new2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result_new2["data"]).to_equal(
        {
            CONF_API_TOKEN: "token3",
            CONF_SITE_ID: other_site.id,
        }
    )


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
) -> None:
    """Test successful reauthentication with new token."""
    site_id = 123456
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "old_token", CONF_SITE_ID: site_id},
        unique_id=str(site_id),
        title="Existing",
    )
    existing.add_to_hass(hass)

    result = await existing.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    site = _make_site(site_id, "ESS")
    vrm_client.users.get_site = AsyncMock(return_value=site)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "new_token"}
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(existing.data[CONF_API_TOKEN]).to_equal("new_token")


@test.cases(
    test.case(
        "auth",
        side_effect=AuthenticationError("bad", status_code=401),
        expected_error="invalid_auth",
    ),
    test.case(
        "vrm",
        side_effect=VictronVRMError("down", status_code=500, response_data={}),
        expected_error="cannot_connect",
    ),
    test.case(
        "site",
        side_effect=SiteNotFound(),
        expected_error="site_not_found",
    ),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vrm_client: AsyncMock = Depends(mock_vrm_client),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Reauth shows errors when validation fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "old", CONF_SITE_ID: 555},
        unique_id="555",
        title="Existing",
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    vrm_client.users.get_site = AsyncMock(side_effect=side_effect)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "bad"}
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": expected_error})

    good_site = _make_site(555, "Existing")
    vrm_client.users.get_site = AsyncMock(return_value=good_site)
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "new_valid"}
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
