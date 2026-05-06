"""Test the Android TV Remote config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from androidtvremote2 import CannotConnect, ConnectionClosed, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.androidtv_remote.config_flow import (
    APPS_NEW_ID,
    CONF_APP_DELETE,
    CONF_APP_ID,
)
from homeassistant.components.androidtv_remote.const import (
    CONF_APP_ICON,
    CONF_APP_NAME,
    CONF_APPS,
    CONF_ENABLE_IME,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_api,
    mock_config_entry,
    mock_setup_entry,
    mock_unload_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test the full user flow from start to finish without any exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal({"host": host, "name": name, "mac": mac})
    expect(result["context"]["source"]).to_equal("user")
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    api.async_finish_pairing.assert_called_with(pin)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_get_name_and_mac raises CannotConnect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(side_effect=CannotConnect())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    api.async_generate_cert_if_missing.assert_called()
    api.async_get_name_and_mac.assert_called()
    api.async_start_pairing.assert_not_called()

    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_finish_pairing = AsyncMock(return_value=None)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal({"host": host, "name": name, "mac": mac})
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_start_pair_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_start_pairing raises CannotConnect in the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_start_pairing = AsyncMock(side_effect=CannotConnect())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    api.async_generate_cert_if_missing.assert_called()
    api.async_get_name_and_mac.assert_called()
    api.async_start_pairing.assert_called()

    pin = "123456"
    api.async_start_pairing = AsyncMock(return_value=None)
    api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect(result["errors"]).to_be_falsy()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_pairing_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_finish_pairing raises InvalidAuth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(side_effect=[InvalidAuth(), None])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    api.async_finish_pairing.assert_called_with(pin)

    expect(api.async_get_name_and_mac.call_count).to_equal(1)
    expect(api.async_start_pairing.call_count).to_equal(1)
    expect(api.async_finish_pairing.call_count).to_equal(1)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal({"host": host, "name": name, "mac": mac})
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    expect(api.async_finish_pairing.call_count).to_equal(2)
    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_pairing_connection_closed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_finish_pairing raises ConnectionClosed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(side_effect=ConnectionClosed())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_finish_pairing.assert_called_with(pin)

    expect(api.async_get_name_and_mac.call_count).to_equal(1)
    expect(api.async_start_pairing.call_count).to_equal(2)
    expect(api.async_finish_pairing.call_count).to_equal(1)

    api.async_finish_pairing = AsyncMock(return_value=None)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal({"host": host, "name": name, "mac": mac})
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_pairing_connection_closed_followed_by_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_finish_pairing raises ConnectionClosed and then async_start_pairing raises CannotConnect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    pin = "123456"

    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))
    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(side_effect=[None, CannotConnect()])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(side_effect=ConnectionClosed())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")

    api.async_finish_pairing.assert_called_with(pin)

    expect(api.async_get_name_and_mac.call_count).to_equal(1)
    expect(api.async_start_pairing.call_count).to_equal(2)
    expect(api.async_finish_pairing.call_count).to_equal(1)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def user_flow_already_configured_host_changed_reloads_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test we abort the user flow if already configured and reload if host changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = "existing name if different is from discovery and should not change"
    host_existing = "1.2.3.45"
    expect(host_existing != host).to_be(True)

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")

    api.async_generate_cert_if_missing.assert_called()
    api.async_get_name_and_mac.assert_called()
    api.async_start_pairing.assert_not_called()

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(2)
    expect(config_entry.data).to_equal(
        {
            "host": host,
            "name": name_existing,
            "mac": mac,
        }
    )


@test
async def user_flow_already_configured_host_not_changed_no_reload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test we abort the user flow if already configured and no reload if host not changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = "existing name if different is from discovery and should not change"
    host_existing = host

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
        state=ConfigEntryState.LOADED,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("host" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(return_value=(name, mac))

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": host}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")

    api.async_generate_cert_if_missing.assert_called()
    api.async_get_name_and_mac.assert_called()
    api.async_start_pairing.assert_not_called()

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(hass.config_entries.async_entries(DOMAIN)[0].data).to_equal(
        {
            "host": host,
            "name": name_existing,
            "mac": mac,
        }
    )


@test
async def zeroconf_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test the full zeroconf flow from start to finish without any exceptions."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["data_schema"]).to_be_falsy()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["context"]["source"]).to_equal("zeroconf")
    expect(result["context"]["unique_id"]).to_equal(unique_id)
    expect(result["context"]["title_placeholders"]).to_equal({"name": name})

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal(
        {
            "host": host,
            "name": name,
            "mac": mac,
        }
    )
    expect(result["context"]["source"]).to_equal("zeroconf")
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    api.async_finish_pairing.assert_called_with(pin)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_start_pairing raises CannotConnect in the zeroconf flow."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["data_schema"]).to_be_falsy()

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(side_effect=CannotConnect())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def zeroconf_flow_pairing_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_finish_pairing raises InvalidAuth in the zeroconf flow."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["data_schema"]).to_be_falsy()

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(side_effect=[InvalidAuth(), None])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    api.async_finish_pairing.assert_called_with(pin)

    expect(api.async_get_name_and_mac.call_count).to_equal(0)
    expect(api.async_start_pairing.call_count).to_equal(1)
    expect(api.async_finish_pairing.call_count).to_equal(1)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(name)
    expect(result["data"]).to_equal({"host": host, "name": name, "mac": mac})
    expect(result["context"]["unique_id"]).to_equal(unique_id)

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_flow_already_configured_host_changed_reloads_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test we abort the zeroconf flow if already configured and reload if host or name changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = "existing name should change since we prefer one from discovery"
    host_existing = "1.2.3.45"
    expect(host_existing != host).to_be(True)
    expect(name_existing != name).to_be(True)

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    await hass.async_block_till_done()
    expect(config_entry.data).to_equal(
        {
            "host": host,
            "name": name,
            "mac": mac,
        }
    )
    expect(len(unload_entry.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(2)


@test
async def zeroconf_flow_already_configured_host_not_changed_no_reload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test we abort the zeroconf flow if already configured and no reload if host and name not changed."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = name
    host_existing = host

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
        state=ConfigEntryState.LOADED,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries(DOMAIN)[0].data).to_equal(
        {
            "host": host,
            "name": name,
            "mac": mac,
        }
    )
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def zeroconf_flow_abort_if_mac_is_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when mac is missing in the zeroconf discovery we abort."""
    host = "1.2.3.4"
    name = "My Android TV"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(host),
            ip_addresses=[ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_already_configured_zeroconf_has_multiple_invalid_ip_addresses(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test we abort the zeroconf flow if already configured and zeroconf has invalid ip addresses."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    name_existing = name
    host_existing = host

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host_existing,
            "name": name_existing,
            "mac": mac,
        },
        unique_id=unique_id,
        state=ConfigEntryState.LOADED,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.2.3.5"),
            ip_addresses=[ip_address("1.2.3.5"), ip_address(host)],
            port=6466,
            hostname=host,
            type="mock_type",
            name=name + "._androidtvremote2._tcp.local.",
            properties={"bt": mac},
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries(DOMAIN)[0].data).to_equal(
        {
            "host": host,
            "name": name,
            "mac": mac,
        }
    )
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test the full reauth flow from start to finish without any exceptions."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"
    pin = "123456"

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host,
            "name": name,
            "mac": mac,
        },
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["context"]["source"]).to_equal("reauth")
    expect(result["context"]["unique_id"]).to_equal(unique_id)
    expect(result["context"]["title_placeholders"]).to_equal({"name": name})

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pair")
    expect("pin" in result["data_schema"].schema).to_be(True)
    expect(result["errors"]).to_be_falsy()

    api.async_get_name_and_mac.assert_not_called()
    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    api.async_finish_pairing = AsyncMock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": pin}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    api.async_finish_pairing.assert_called_with(pin)

    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries(DOMAIN)[0].data).to_equal(
        {
            "host": host,
            "name": name,
            "mac": mac,
        }
    )
    expect(len(unload_entry.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(2)


@test
async def reauth_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    unload_entry: AsyncMock = Depends(mock_unload_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test async_start_pairing raises CannotConnect in the reauth flow."""
    host = "1.2.3.4"
    name = "My Android TV"
    mac = "1A:2B:3C:4D:5E:6F"
    unique_id = "1a:2b:3c:4d:5e:6f"

    config_entry = MockConfigEntry(
        title=name,
        domain=DOMAIN,
        data={
            "host": host,
            "name": name,
            "mac": mac,
        },
        unique_id=unique_id,
        state=ConfigEntryState.LOADED,
    )
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["context"]["source"]).to_equal("reauth")
    expect(result["context"]["unique_id"]).to_equal(unique_id)
    expect(result["context"]["title_placeholders"]).to_equal({"name": name})

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_start_pairing = AsyncMock(side_effect=CannotConnect())

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    api.async_get_name_and_mac.assert_not_called()
    api.async_generate_cert_if_missing.assert_called()
    api.async_start_pairing.assert_called()

    await hass.async_block_till_done()
    expect(len(unload_entry.mock_calls)).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(api.disconnect.call_count).to_equal(0)
    expect(api.async_connect.call_count).to_equal(1)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal({CONF_APPS, CONF_ENABLE_IME})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: False},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_ENABLE_IME: False})
    await hass.async_block_till_done()

    expect(api.disconnect.call_count).to_equal(1)
    expect(api.async_connect.call_count).to_equal(2)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: False},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_ENABLE_IME: False})
    await hass.async_block_till_done()

    expect(api.disconnect.call_count).to_equal(1)
    expect(api.async_connect.call_count).to_equal(2)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: True},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_ENABLE_IME: True})
    await hass.async_block_till_done()

    expect(api.disconnect.call_count).to_equal(2)
    expect(api.async_connect.call_count).to_equal(3)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APPS: APPS_NEW_ID,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("apps")
    expect(result["description_placeholders"]).to_equal(
        {
            "app_id": "",
            "example_app_id": "com.plexapp.android",
            "example_app_play_store_url": "https://play.google.com/store/apps/details?id=com.plexapp.android",
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APP_ID: "app1",
            CONF_APP_NAME: "App1",
            CONF_APP_ICON: "Icon1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APPS: "app1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("apps")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APP_NAME: "Application1",
            CONF_APP_ICON: "Icon1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_APPS: {"app1": {CONF_APP_NAME: "Application1", CONF_APP_ICON: "Icon1"}},
            CONF_ENABLE_IME: True,
        }
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APPS: "app1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("apps")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APP_DELETE: True,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_ENABLE_IME: True})


@test
async def reconfigure_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test the full reconfigure flow from start to finish without any exceptions."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_be_falsy()
    expect("host" in result["data_schema"].schema).to_be(True)
    host_key = next(k for k in result["data_schema"].schema if k.schema == "host")
    expect(host_key.default()).to_equal(config_entry.data["host"])

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(
        return_value=(config_entry.data["name"], config_entry.data["mac"])
    )

    new_host = "4.3.2.1"
    expect(new_host != config_entry.data["host"]).to_be(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data["host"]).to_equal(new_host)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reconfigure_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test reconfigure flow with CannotConnect exception."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    api.async_get_name_and_mac = AsyncMock(
        side_effect=[
            CannotConnect(),
            (config_entry.data["name"], config_entry.data["mac"]),
        ]
    )

    new_host = "4.3.2.1"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(config_entry.data["host"]).to_equal("1.2.3.4")
    expect(len(setup_entry.mock_calls)).to_equal(0)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data["host"]).to_equal(new_host)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reconfigure_flow_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test reconfigure flow with a different device (unique_id mismatch)."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    new_mac = "FF:EE:DD:CC:BB:AA"
    expect(new_mac != config_entry.data["mac"]).to_be(True)
    api.async_get_name_and_mac = AsyncMock(return_value=("name", new_mac))

    new_host = "4.3.2.1"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(config_entry.data["host"]).to_equal("1.2.3.4")
    expect(len(setup_entry.mock_calls)).to_equal(0)
