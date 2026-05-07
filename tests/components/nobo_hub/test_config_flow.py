"""Test the Nobø Ecohub config flow."""

from unittest.mock import AsyncMock, PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nobo_hub.const import CONF_OVERRIDE_TYPE, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_unload_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture."""


@test
async def configure_with_discover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
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
        {"device": "1.1.1.1"},
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
            {"serial_suffix": "012"},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal("My Nobø Ecohub")
        expect(result3["data"]).to_equal(
            {"ip_address": "1.1.1.1", "serial": "123456789012"}
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        setup_entry.assert_awaited_once()


@test
async def configure_manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test manual configuration when no hubs are discovered."""
    with patch("pynobo.nobo.async_discover_hubs", return_value=[]):
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
            {"serial": "123456789012", "ip_address": "1.1.1.1"},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("My Nobø Ecohub")
        expect(result2["data"]).to_equal(
            {"serial": "123456789012", "ip_address": "1.1.1.1"}
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        setup_entry.assert_awaited_once()


@test
async def configure_user_selected_manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
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
        {"device": "manual"},
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
            {"serial": "123456789012", "ip_address": "1.1.1.1"},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("My Nobø Ecohub")
        expect(result2["data"]).to_equal(
            {"serial": "123456789012", "ip_address": "1.1.1.1"}
        )
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        setup_entry.assert_awaited_once()


@test
async def configure_invalid_serial_suffix(
    _trigger: None = Depends(_trigger_executor),
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
        {"device": "1.1.1.1"},
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {"serial_suffix": "ABC"},
    )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "invalid_serial"})


@test
async def configure_invalid_serial_undiscovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid serial error."""
    with patch("pynobo.nobo.async_discover_hubs", return_value=[]):
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
    _trigger: None = Depends(_trigger_executor),
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


@test.cases(
    test.case("serial_mismatch", connect_outcome={"return_value": False}, expected_error="cannot_connect"),
    test.case("tcp_failure", connect_outcome={"side_effect": ConnectionRefusedError(61, "")}, expected_error="cannot_connect_ip"),
)
async def configure_cannot_connect(
    connect_outcome: dict[str, object],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Connect failures map to distinct error keys."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device": "1.1.1.1"},
    )

    with patch("pynobo.nobo.async_connect_hub", **connect_outcome) as mock_connect:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"serial_suffix": "012"},
        )
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["errors"]).to_equal({"base": expected_error})
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
) -> None:
    """Test the options flow."""
    config_entry = MockConfigEntry(
        domain="nobo_hub",
        unique_id="123456789012",
        data={"serial": "123456789012", "ip_address": "1.1.1.1", "auto_discover": True},
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    setup_entry.reset_mock()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_OVERRIDE_TYPE: "constant"},
    )
    await hass.async_block_till_done()

    expect(unload_entry.await_count).to_equal(1)
    expect(setup_entry.await_count).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_OVERRIDE_TYPE: "constant"})
    unload_entry.reset_mock()
    setup_entry.reset_mock()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_OVERRIDE_TYPE: "now"},
    )
    await hass.async_block_till_done()

    expect(unload_entry.await_count).to_equal(1)
    expect(setup_entry.await_count).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_OVERRIDE_TYPE: "now"})
