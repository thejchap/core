"""Define tests for the Awair config flow."""

from typing import Any
from unittest.mock import MagicMock, Mock, patch

from aiohttp.client_exceptions import ClientConnectorError
from python_awair.exceptions import AuthError, AwairError
from tryke import Depends, expect, fixture, test

from homeassistant.components.awair.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import (
    CLOUD_CONFIG,
    CLOUD_UNIQUE_ID,
    LOCAL_CONFIG,
    LOCAL_UNIQUE_ID,
    ZEROCONF_DISCOVERY,
)

from tests.common import MockConfigEntry
from tests.components.awair._fixtures import (
    cloud_devices,
    local_devices,
    mock_zeroconf,
    no_devices,
    user,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def show_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.MENU).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def invalid_access_token(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when the access token is invalid."""
    with patch("python_awair.AwairClient.query", side_effect=AuthError()):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CLOUD_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "cloud"},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            CLOUD_CONFIG,
        )

        expect(result["errors"]).to_equal({CONF_ACCESS_TOKEN: "invalid_access_token"})


@test
async def unexpected_api_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that we abort on generic errors."""
    with patch("python_awair.AwairClient.query", side_effect=AwairError()):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CLOUD_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "cloud"},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            CLOUD_CONFIG,
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("unknown")


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    user: Any = Depends(user),
    cloud_devices: Any = Depends(cloud_devices),
) -> None:
    """Test that errors are shown when adding a duplicate config."""
    with patch(
        "python_awair.AwairClient.query",
        side_effect=[user, cloud_devices],
    ):
        MockConfigEntry(
            domain=DOMAIN, unique_id=CLOUD_UNIQUE_ID, data=CLOUD_CONFIG
        ).add_to_hass(hass)

        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CLOUD_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "cloud"},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            CLOUD_CONFIG,
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured_account")


@test
async def no_devices_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    user: Any = Depends(user),
    no_devices: Any = Depends(no_devices),
) -> None:
    """Test that errors are shown when the API returns no devices."""
    with patch("python_awair.AwairClient.query", side_effect=[user, no_devices]):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CLOUD_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "cloud"},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            CLOUD_CONFIG,
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("no_devices_found")


@test
async def reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    user: Any = Depends(user),
    cloud_devices: Any = Depends(cloud_devices),
) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CLOUD_UNIQUE_ID,
        data={**CLOUD_CONFIG, CONF_ACCESS_TOKEN: "blah"},
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with patch("python_awair.AwairClient.query", side_effect=AuthError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ACCESS_TOKEN: "bad"},
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({CONF_ACCESS_TOKEN: "invalid_access_token"})

    with (
        patch(
            "python_awair.AwairClient.query",
            side_effect=[user, cloud_devices],
        ),
        patch(
            "homeassistant.components.awair.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ACCESS_TOKEN: "good"},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(dict(mock_config.data)).to_equal({CONF_ACCESS_TOKEN: "good"})


@test
async def reauth_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CLOUD_UNIQUE_ID,
        data={**CLOUD_CONFIG, CONF_ACCESS_TOKEN: "blah"},
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    with patch("python_awair.AwairClient.query", side_effect=AwairError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CLOUD_CONFIG,
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("unknown")


@test
async def create_cloud_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    user: Any = Depends(user),
    cloud_devices: Any = Depends(cloud_devices),
) -> None:
    """Test overall flow when using cloud api."""
    with (
        patch(
            "python_awair.AwairClient.query",
            side_effect=[user, cloud_devices],
        ),
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ),
    ):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CLOUD_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "cloud"},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            CLOUD_CONFIG,
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("foo@bar.com")
        expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(
            CLOUD_CONFIG[CONF_ACCESS_TOKEN]
        )
        expect(result["result"].unique_id).to_equal(CLOUD_UNIQUE_ID)


@test
async def create_local_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    local_devices: Any = Depends(local_devices),
) -> None:
    """Test overall flow when using local API."""
    with (
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ),
    ):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=LOCAL_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "local"},
        )

        form_step = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            {},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            LOCAL_CONFIG,
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("Awair Element (24947)")
        expect(result["data"][CONF_HOST]).to_equal(LOCAL_CONFIG[CONF_HOST])
        expect(result["result"].unique_id).to_equal(LOCAL_UNIQUE_ID)


@test
async def create_local_entry_from_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    local_devices: Any = Depends(local_devices),
) -> None:
    """Test local API when device discovered after instructions shown."""
    menu_step = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=LOCAL_CONFIG
    )

    form_step = await hass.config_entries.flow.async_configure(
        menu_step["flow_id"],
        {"next_step_id": "local"},
    )

    with patch("python_awair.AwairClient.query", side_effect=[local_devices]):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            data=Mock(host=LOCAL_CONFIG[CONF_HOST]),
            context={"source": SOURCE_ZEROCONF},
        )

    form_step = await hass.config_entries.flow.async_configure(
        form_step["flow_id"],
        {},
    )

    with (
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            {"device": LOCAL_CONFIG[CONF_HOST]},
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Awair Element (24947)")
    expect(result["data"][CONF_HOST]).to_equal(LOCAL_CONFIG[CONF_HOST])
    expect(result["result"].unique_id).to_equal(LOCAL_UNIQUE_ID)


@test
async def create_local_entry_awair_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test overall flow when using local API and device is returns error."""
    with patch(
        "python_awair.AwairClient.query",
        side_effect=AwairError(),
    ):
        menu_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=LOCAL_CONFIG
        )

        form_step = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "local"},
        )

        form_step = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            {},
        )

        result = await hass.config_entries.flow.async_configure(
            form_step["flow_id"],
            LOCAL_CONFIG,
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("local_pick")


@test
async def create_zeroconf_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    local_devices: Any = Depends(local_devices),
) -> None:
    """Test overall flow when using discovery."""
    with (
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ),
    ):
        confirm_step = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
        )

        result = await hass.config_entries.flow.async_configure(
            confirm_step["flow_id"],
            {},
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("Awair Element (24947)")
        expect(result["data"][CONF_HOST]).to_equal(ZEROCONF_DISCOVERY.host)
        expect(result["result"].unique_id).to_equal(LOCAL_UNIQUE_ID)


@test
async def unsuccessful_create_zeroconf_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test overall flow when using discovery and device is unreachable."""
    with patch(
        "python_awair.AwairClient.query",
        side_effect=ClientConnectorError(Mock(), OSError()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)


@test
async def zeroconf_discovery_update_configuration(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    local_devices: Any = Depends(local_devices),
) -> None:
    """Test updating an existing Awair config entry with discovery info."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1"},
        unique_id=LOCAL_UNIQUE_ID,
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZEROCONF_DISCOVERY,
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured_device")

        expect(config_entry.data[CONF_HOST]).to_equal(ZEROCONF_DISCOVERY.host)
        expect(mock_setup_entry.call_count).to_equal(0)


@test
async def zeroconf_during_onboarding(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    local_devices: Any = Depends(local_devices),
) -> None:
    """Test the zeroconf creates an entry during onboarding."""
    with (
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
        patch(
            "homeassistant.components.onboarding.async_is_onboarded",
            return_value=False,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
        )

    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result.get("title")).to_equal("Awair Element (24947)")
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(ZEROCONF_DISCOVERY.host)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal(LOCAL_UNIQUE_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
