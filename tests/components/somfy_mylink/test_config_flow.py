"""Test the Somfy MyLink config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.somfy_mylink.const import (
    CONF_REVERSED_TARGET_IDS,
    CONF_SYSTEM_ID,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_user(
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
        patch(
            "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
            return_value={"any": "data"},
        ),
        patch(
            "homeassistant.components.somfy_mylink.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("MyLink 1.1.1.1")
    expect(result2["data"]).to_equal(
        {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.1.1.1", CONF_PORT: 12, CONF_SYSTEM_ID: 46},
    )
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
            return_value={"any": "data"},
        ),
        patch(
            "homeassistant.components.somfy_mylink.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
        return_value={
            "jsonrpc": "2.0",
            "error": {"code": -32652, "message": "Invalid auth"},
            "id": 818,
        },
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle broad exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
        side_effect=ValueError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def options_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options will not display until loaded."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.1.1.1", CONF_PORT: 12, CONF_SYSTEM_ID: "46"},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.somfy_mylink.SomfyMyLinkSynergy.status_info",
        return_value={"result": []},
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.ABORT)


@test.cases(
    test.case("reversed_true", reversed=True),
    test.case("reversed_false", reversed=False),
)
async def options_with_targets(
    reversed: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can configure reverse for a target."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.1.1.1", CONF_PORT: 12, CONF_SYSTEM_ID: "46"},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.somfy_mylink.SomfyMyLinkSynergy.status_info",
        return_value={
            "result": [{"targetID": "a", "name": "Master Window", "type": 0}]
        },
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(
            True
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={"target_id": "a"}
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"], user_input={"reverse": reversed}
        )

        expect(result3["type"]).to_be(FlowResultType.FORM)

        result4 = await hass.config_entries.options.async_configure(
            result3["flow_id"], user_input={"target_id": None}
        )
        expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)

        expect(config_entry.options).to_equal(
            {CONF_REVERSED_TARGET_IDS: {"a": reversed}}
        )

        await hass.async_block_till_done()


@test
async def form_user_already_configured_from_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if already configured from dhcp."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.1.1.1", CONF_PORT: 12, CONF_SYSTEM_ID: 46},
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
            return_value={"any": "data"},
        ),
        patch(
            "homeassistant.components.somfy_mylink.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1", macaddress="aabbccddeeff", hostname="somfy_eeff"
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def already_configured_with_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ignored entries do not break checking for existing entries."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.1", macaddress="aabbccddeeff", hostname="somfy_eeff"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can process the discovery from dhcp."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.1", macaddress="aabbccddeeff", hostname="somfy_eeff"
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.somfy_mylink.config_flow.SomfyMyLinkSynergy.status_info",
            return_value={"any": "data"},
        ),
        patch(
            "homeassistant.components.somfy_mylink.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("MyLink 1.1.1.1")
    expect(result2["data"]).to_equal(
        {CONF_HOST: "1.1.1.1", CONF_PORT: 1234, CONF_SYSTEM_ID: "456"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
