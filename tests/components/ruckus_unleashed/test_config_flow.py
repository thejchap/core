"""Test the config flow."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from aioruckus.const import (
    ERROR_CONNECT_TEMPORARY,
    ERROR_CONNECT_TIMEOUT,
    ERROR_LOGIN_INCORRECT,
)
from aioruckus.exceptions import AuthenticationError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ruckus_unleashed.const import (
    API_CLIENT_MAC,
    API_SYS_SYSINFO,
    API_SYS_SYSINFO_SERIAL,
    CONF_MAC_FILTER,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import utcnow

from . import (
    CONFIG,
    DEFAULT_SYSTEM_INFO,
    DEFAULT_TITLE,
    TEST_CLIENT,
    RuckusAjaxApiPatchContext,
    init_integration,
    mock_config_entry,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import entity_registry as entity_registry_fx, hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        RuckusAjaxApiPatchContext(),
        patch(
            "homeassistant.components.ruckus_unleashed.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )
        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(DEFAULT_TITLE)
    expect(result2["data"]).to_equal(CONFIG)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with RuckusAjaxApiPatchContext(
        login_mock=AsyncMock(side_effect=AuthenticationError(ERROR_LOGIN_INCORRECT))
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_user_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def form_user_reauth_different_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    system_info = deepcopy(DEFAULT_SYSTEM_INFO)
    system_info[API_SYS_SYSINFO][API_SYS_SYSINFO_SERIAL] = "000000000"
    with RuckusAjaxApiPatchContext(system_info=system_info):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("invalid_host")


@test
async def form_user_reauth_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with RuckusAjaxApiPatchContext(
        login_mock=AsyncMock(side_effect=AuthenticationError(ERROR_LOGIN_INCORRECT))
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_user_reauth_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with RuckusAjaxApiPatchContext(
        login_mock=AsyncMock(side_effect=ConnectionError(ERROR_CONNECT_TIMEOUT))
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_user_reauth_general_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with RuckusAjaxApiPatchContext(login_mock=AsyncMock(side_effect=Exception)):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with RuckusAjaxApiPatchContext(
        login_mock=AsyncMock(side_effect=ConnectionError(ERROR_CONNECT_TIMEOUT))
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_general_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with RuckusAjaxApiPatchContext(login_mock=AsyncMock(side_effect=Exception)):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_unexpected_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with RuckusAjaxApiPatchContext(
        login_mock=AsyncMock(
            side_effect=ConnectionRefusedError(ERROR_CONNECT_TEMPORARY)
        )
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle duplicate error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with RuckusAjaxApiPatchContext():
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

        future = utcnow() + timedelta(minutes=60)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow shows form and accepts selection."""
    entry = await init_integration(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MAC_FILTER: [TEST_CLIENT[API_CLIENT_MAC]]},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_MAC_FILTER]).to_equal([TEST_CLIENT[API_CLIENT_MAC]])


@test
async def options_flow_offline_clients_preserved(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test previously selected but now-offline clients remain selectable."""
    offline_mac = "FF:EE:DD:CC:BB:AA"
    entry = await init_integration(hass)
    hass.config_entries.async_update_entry(
        entry, options={CONF_MAC_FILTER: [offline_mac]}
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MAC_FILTER: [offline_mac]},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_MAC_FILTER]).to_equal([offline_mac])


@test
async def options_flow_removes_deselected_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test that deselected devices have their entities removed."""
    entry = await init_integration(hass)

    expect(
        bool(
            entity_registry.async_get_entity_id(
                "device_tracker", DOMAIN, TEST_CLIENT[API_CLIENT_MAC]
            )
        )
    ).to_be(True)

    offline_mac = "FF:EE:DD:CC:BB:AA"
    hass.config_entries.async_update_entry(
        entry,
        options={CONF_MAC_FILTER: [TEST_CLIENT[API_CLIENT_MAC], offline_mac]},
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MAC_FILTER: [offline_mac]},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(
        bool(
            entity_registry.async_get_entity_id(
                "device_tracker", DOMAIN, TEST_CLIENT[API_CLIENT_MAC]
            )
        )
    ).to_be(False)


@test
async def options_flow_clear_filter_keeps_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test that clearing the filter does not remove entities."""
    entry = await init_integration(hass)

    expect(
        bool(
            entity_registry.async_get_entity_id(
                "device_tracker", DOMAIN, TEST_CLIENT[API_CLIENT_MAC]
            )
        )
    ).to_be(True)

    hass.config_entries.async_update_entry(
        entry,
        options={CONF_MAC_FILTER: [TEST_CLIENT[API_CLIENT_MAC]]},
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_MAC_FILTER: []},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_MAC_FILTER]).to_equal([])

    expect(
        bool(
            entity_registry.async_get_entity_id(
                "device_tracker", DOMAIN, TEST_CLIENT[API_CLIENT_MAC]
            )
        )
    ).to_be(True)
