"""Test the Nobø Ecohub config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nobo_hub.const import CONF_OVERRIDE_TYPE, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nobo_hub._fixtures import mock_setup_entry, mock_unload_entry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def configure_with_discover(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test configure with discover."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "device": "1.1.1.1",
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({})
    expect(result2["step_id"]).to_equal("selected")

    with (
        patch("pynobo.nobo.async_connect_hub", return_value=True) as mock_connect,
        patch(
            "pynobo.nobo.hub_info",
            new_callable=PropertyMock,
            create=True,
            return_value={"name": "My Nobø Ecohub"},
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "serial_suffix": "012",
            },
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal("My Nobø Ecohub")
        expect(result3["data"]).to_equal(
            {
                "ip_address": "1.1.1.1",
                "serial": "123456789012",
                "auto_discovered": True,
            }
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        mock_setup.assert_awaited_once()


@test
async def configure_manual(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test manual configuration when no hubs are discovered."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})
        expect(result["step_id"]).to_equal("manual")

    with (
        patch("pynobo.nobo.async_connect_hub", return_value=True) as mock_connect,
        patch(
            "pynobo.nobo.hub_info",
            new_callable=PropertyMock,
            create=True,
            return_value={"name": "My Nobø Ecohub"},
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "serial": "123456789012",
                "ip_address": "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("My Nobø Ecohub")
        expect(result2["data"]).to_equal(
            {
                "serial": "123456789012",
                "ip_address": "1.1.1.1",
                "auto_discovered": False,
            }
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        mock_setup.assert_awaited_once()


@test
async def configure_user_selected_manual(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test configuration when user selects manual."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "device": "manual",
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({})
    expect(result2["step_id"]).to_equal("manual")

    with (
        patch("pynobo.nobo.async_connect_hub", return_value=True) as mock_connect,
        patch(
            "pynobo.nobo.hub_info",
            new_callable=PropertyMock,
            create=True,
            return_value={"name": "My Nobø Ecohub"},
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "serial": "123456789012",
                "ip_address": "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("My Nobø Ecohub")
        expect(result2["data"]).to_equal(
            {
                "serial": "123456789012",
                "ip_address": "1.1.1.1",
                "auto_discovered": False,
            }
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        mock_setup.assert_awaited_once()


@test
async def configure_invalid_serial_suffix(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid serial suffix error."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "device": "1.1.1.1",
        },
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {"serial_suffix": "ABC"},
    )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "invalid_serial"})


@test
async def configure_invalid_serial_undiscovered(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid serial error."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"ip_address": "1.1.1.1", "serial": "123456789"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_serial"})


@test
async def configure_invalid_ip_address(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid ip address error."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"serial": "123456789012", "ip_address": "ABCD"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_ip"})


@test
async def configure_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "device": "1.1.1.1",
        },
    )

    with patch(
        "pynobo.nobo.async_connect_hub",
        return_value=False,
    ) as mock_connect:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"serial_suffix": "012"},
        )
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["errors"]).to_equal({"base": "cannot_connect"})
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
    mock_unload: AsyncMock = Depends(mock_unload_entry),
) -> None:
    """Test the options flow."""
    config_entry = MockConfigEntry(
        domain="nobo_hub",
        unique_id="123456789012",
        data={"serial": "123456789012", "ip_address": "1.1.1.1", "auto_discover": True},
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    mock_setup.reset_mock()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_OVERRIDE_TYPE: "Constant",
        },
    )
    await hass.async_block_till_done()

    expect(mock_unload.await_count).to_equal(1)
    expect(mock_setup.await_count).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_OVERRIDE_TYPE: "Constant"})
    mock_unload.reset_mock()
    mock_setup.reset_mock()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_OVERRIDE_TYPE: "Now",
        },
    )
    await hass.async_block_till_done()

    expect(mock_unload.await_count).to_equal(1)
    expect(mock_setup.await_count).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_OVERRIDE_TYPE: "Now"})
