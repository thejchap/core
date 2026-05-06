"""Test the SFR Box config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from sfrbox_api.exceptions import SFRBoxAuthenticationError, SFRBoxError
from sfrbox_api.models import SystemInfo
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sfr_box.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import config_entry, config_entry_with_auth, mock_setup_entry

from tests.common import async_load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow_skip_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow (no authentication)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SFR Box")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.0.1"})
    expect(result["context"]["unique_id"]).to_equal("e4:5d:51:00:11:22")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_skip_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow (no authentication) with failure and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        side_effect=SFRBoxError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SFR Box")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.0.1"})
    expect(result["context"]["unique_id"]).to_equal("e4:5d:51:00:11:22")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_with_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow (with authentication)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "auth"},
    )

    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "valid"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SFR Box")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "valid",
        }
    )
    expect(result["context"]["unique_id"]).to_equal("e4:5d:51:00:11:22")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_with_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow (with authentication) with failure and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "auth"},
    )

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.authenticate",
        side_effect=SFRBoxAuthenticationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "invalid"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "valid"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SFR Box")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "valid",
        }
    )
    expect(result["context"]["unique_id"]).to_equal("e4:5d:51:00:11:22")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_duplicate_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _entry: ConfigEntry = Depends(config_entry),
) -> None:
    """Test abort if unique_id configured."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    system_info = SystemInfo(
        **(await async_load_json_object_fixture(hass, "system_getInfo.json", DOMAIN))
    )
    system_info.mac_addr = "aa:bb:cc:dd:ee:ff"
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=system_info,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def config_flow_duplicate_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _entry: ConfigEntry = Depends(config_entry),
) -> None:
    """Test abort if unique_id configured."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    system_info = SystemInfo(
        **(await async_load_json_object_fixture(hass, "system_getInfo.json", DOMAIN))
    )
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=system_info,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.2"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: ConfigEntry = Depends(config_entry_with_auth),
) -> None:
    """Test the start of the config flow."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.authenticate",
        side_effect=SFRBoxAuthenticationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "invalid"},
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "invalid_auth"})

    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "new_password"},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")


@test
async def reconfigure_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: ConfigEntry = Depends(config_entry),
) -> None:
    """Test reconfigure host on a simple (no-auth) entry."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    expect(entry.data[CONF_HOST]).to_equal("192.168.0.1")
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.100"},
        )

    expect(result.get("type")).to_be(FlowResultType.MENU)
    expect(result.get("step_id")).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_HOST: "192.168.0.100"})


@test
async def reconfigure_add_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: ConfigEntry = Depends(config_entry),
) -> None:
    """Test reconfigure able to add authentication on a simple (no-auth) entry."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    expect(CONF_USERNAME not in entry.data).to_be(True)
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result.get("type")).to_be(FlowResultType.MENU)
    expect(result.get("step_id")).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "auth"},
    )

    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "admin", CONF_PASSWORD: "valid"},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_HOST: "192.168.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "valid",
        }
    )


@test
async def reconfigure_clear_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: ConfigEntry = Depends(config_entry_with_auth),
) -> None:
    """Test reconfigure clears authentication on an entry with auth."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    expect(entry.data[CONF_USERNAME]).to_equal("admin")
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
                | {"mac_addr": "e4:5d:51:00:11:23"}
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result.get("type")).to_be(FlowResultType.MENU)
    expect(result.get("step_id")).to_equal("choose_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(CONF_USERNAME not in entry.data).to_be(True)


@test
async def reconfigure_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: ConfigEntry = Depends(config_entry_with_auth),
) -> None:
    """Test reconfigure fails if the unique ID (=MAC) does not match."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    expect(entry.data[CONF_USERNAME]).to_equal("admin")
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.0.1"},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("unique_id_mismatch")
