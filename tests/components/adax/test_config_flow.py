"""Test the Adax config flow."""

from unittest.mock import patch

import adax_local
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.adax.const import (
    ACCOUNT_ID,
    CLOUD,
    CONNECTION_TYPE,
    DOMAIN,
    LOCAL,
    WIFI_PSWD,
    WIFI_SSID,
)
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network

TEST_DATA = {
    ACCOUNT_ID: 12345,
    CONF_PASSWORD: "pswd",
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    with (
        patch(
            "adax.get_adax_token",
            return_value="test_token",
        ),
        patch(
            "homeassistant.components.adax.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal(str(TEST_DATA["account_id"]))
    expect(result3["data"]).to_equal(
        {
            ACCOUNT_ID: TEST_DATA["account_id"],
            CONF_PASSWORD: TEST_DATA["password"],
            CONNECTION_TYPE: CLOUD,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    with patch(
        "adax.get_adax_token",
        return_value=None,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            TEST_DATA,
        )
    expect(result3["type"] is FlowResultType.FORM).to_be(True)
    expect(result3["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_entry_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test user input for config_entry that already exists."""

    first_entry = MockConfigEntry(
        domain="adax",
        data=TEST_DATA,
        unique_id=str(TEST_DATA[ACCOUNT_ID]),
    )
    first_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    with patch("adax.get_adax_token", return_value="token"):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.ABORT).to_be(True)
    expect(result3["reason"]).to_equal("already_configured")


@test
async def local_create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test create entry from user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with (
        patch(
            "homeassistant.components.adax.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.adax.config_flow.adax_local.AdaxConfig",
            autospec=True,
        ) as mock_client_class,
    ):
        client = mock_client_class.return_value
        client.configure_device.return_value = True
        client.device_ip = "192.168.1.4"
        client.access_token = "token"
        client.mac_id = "8383838"
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    test_data[CONNECTION_TYPE] = LOCAL
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("8383838")
    expect(result["data"]).to_equal(
        {
            "connection_type": "Local",
            "ip_address": "192.168.1.4",
            "token": "token",
            "unique_id": "8383838",
        }
    )


@test
async def local_flow_entry_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test user input for config_entry that already exists."""

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    first_entry = MockConfigEntry(
        domain="adax",
        data=test_data,
        unique_id="8383838",
    )
    first_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with patch("adax_local.AdaxConfig", autospec=True) as mock_client_class:
        client = mock_client_class.return_value
        client.configure_device.return_value = True
        client.device_ip = "192.168.1.4"
        client.access_token = "token"
        client.mac_id = "8383838"

        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def local_connection_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test connection error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with patch(
        "homeassistant.components.adax.config_flow.adax_local.AdaxConfig.configure_device",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def local_heater_not_available(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test connection error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with patch(
        "homeassistant.components.adax.config_flow.adax_local.AdaxConfig.configure_device",
        side_effect=adax_local.HeaterNotAvailable,
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("heater_not_available")


@test
async def local_heater_not_found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test connection error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with patch(
        "homeassistant.components.adax.config_flow.adax_local.AdaxConfig.configure_device",
        side_effect=adax_local.HeaterNotFound,
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("heater_not_found")


@test
async def local_invalid_wifi_cred(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test connection error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: LOCAL,
        },
    )
    expect(result2["type"] is FlowResultType.FORM).to_be(True)

    test_data = {
        WIFI_SSID: "ssid",
        WIFI_PSWD: "pswd",
    }

    with patch(
        "homeassistant.components.adax.config_flow.adax_local.AdaxConfig.configure_device",
        side_effect=adax_local.InvalidWifiCred,
    ):
        result = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            test_data,
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("invalid_auth")
