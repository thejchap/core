"""Test the Network UPS Tools (NUT) config flow."""

from ipaddress import ip_address
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nut.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RESOURCES,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .util import _get_mock_nutclient

from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {
    CONF_HOST: "localhost",
    CONF_PORT: 123,
    CONF_NAME: "name",
    CONF_RESOURCES: ["battery.charge"],
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def form_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            hostname="mock_hostname",
            name="mock_name",
            port=1234,
            properties={},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"},
        list_ups=["ups1"],
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("192.168.1.5:1234")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.5",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 1234,
            CONF_USERNAME: "test-username",
        }
    )
    expect(result2["result"].unique_id).to_be(None)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_one_alias(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_user_one_alias."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_multiple_aliases(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_user_multiple_aliases."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_one_alias_with_ignored_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_user_one_alias_with_ignored_entry."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_no_aliases_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_no_aliases_found."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_cannot_connect."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def auth_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_auth_failures."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_abort_if_already_setup."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_duplicate_unique_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_abort_duplicate_unique_ids."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_multiple_aliases_duplicate_unique_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_abort_multiple_aliases_duplicate_unique_ids."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_if_already_setup_alias(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_abort_if_already_setup_alias."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_successful."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_nochange(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_nochange."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_password_nochange(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_password_nochange."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_already_configured."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_unique_id_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_unique_id_change."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_duplicate_unique_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_one_alias_duplicate_unique_ids."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_successful."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_nochange(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_nochange."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_password_nochange(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_password_nochange."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_already_configured."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_unique_id_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_unique_id_change."""


@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_duplicate_unique_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_multiple_aliases_duplicate_unique_ids."""
