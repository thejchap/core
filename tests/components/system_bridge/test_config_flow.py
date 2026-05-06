"""Test the System Bridge config flow."""

from unittest.mock import patch

from systembridgeconnector.exceptions import (
    AuthenticationException,
    ConnectionClosedException,
    ConnectionErrorException,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.system_bridge.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    FIXTURE_AUTH_INPUT,
    FIXTURE_DATA_RESPONSE,
    FIXTURE_USER_INPUT,
    FIXTURE_UUID,
    FIXTURE_ZEROCONF,
    FIXTURE_ZEROCONF_BAD,
    FIXTURE_ZEROCONF_INPUT,
    mock_data_listener,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test full user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            return_value=FIXTURE_DATA_RESPONSE,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
        patch(
            "homeassistant.components.system_bridge.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("127.0.0.1")
    expect(result2["data"]).to_equal(FIXTURE_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "systembridgeconnector.websocket_client.WebSocketClient.connect",
        side_effect=ConnectionErrorException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_connection_closed_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle connection closed cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=ConnectionClosedException,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_timeout_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle timeout cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=TimeoutError,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=AuthenticationException,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_uuid_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle error from bad uuid."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=ValueError,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=Exception,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_USER_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth_authorization_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on authorization error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UUID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authenticate")

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=AuthenticationException,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("authenticate")
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def reauth_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on connection error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UUID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authenticate")

    with patch(
        "systembridgeconnector.websocket_client.WebSocketClient.connect",
        side_effect=ConnectionErrorException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("authenticate")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.connect",
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            return_value=None,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["step_id"]).to_equal("authenticate")
    expect(result3["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth_connection_closed_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on connection error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UUID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authenticate")

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            side_effect=ConnectionClosedException,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("authenticate")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UUID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authenticate")

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            return_value=FIXTURE_DATA_RESPONSE,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
        patch(
            "homeassistant.components.system_bridge.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=FIXTURE_ZEROCONF,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with (
        patch(
            "homeassistant.components.system_bridge.config_flow.WebSocketClient.connect"
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.get_data",
            return_value=FIXTURE_DATA_RESPONSE,
        ),
        patch(
            "systembridgeconnector.websocket_client.WebSocketClient.listen",
            new=mock_data_listener,
        ),
        patch(
            "homeassistant.components.system_bridge.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("127.0.0.1")
    expect(result2["data"]).to_equal(FIXTURE_ZEROCONF_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf cannot connect flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=FIXTURE_ZEROCONF,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "systembridgeconnector.websocket_client.WebSocketClient.connect",
        side_effect=ConnectionErrorException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], FIXTURE_AUTH_INPUT
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("authenticate")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def zeroconf_bad_zeroconf_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf cannot connect flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=FIXTURE_ZEROCONF_BAD,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
