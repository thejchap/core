"""Tests for the Minecraft Server config flow."""

from unittest.mock import patch

from mcstatus import BedrockServer, JavaServer, LegacyServer
from tryke import Depends, expect, fixture, test

from homeassistant.components.minecraft_server.api import MinecraftServerType
from homeassistant.components.minecraft_server.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ADDRESS, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    bedrock_mock_config_entry,
    java_mock_config_entry,
    legacy_java_mock_config_entry,
)
from .const import (
    TEST_ADDRESS,
    TEST_BEDROCK_STATUS_RESPONSE,
    TEST_HOST,
    TEST_JAVA_STATUS_RESPONSE,
    TEST_LEGACY_JAVA_STATUS_RESPONSE,
    TEST_PORT,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


USER_INPUT = {
    CONF_ADDRESS: TEST_ADDRESS,
}


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow_java(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config entry for a Java Edition server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            return_value=JavaServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_status",
            return_value=TEST_JAVA_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result["data"][CONF_TYPE]).to_equal(MinecraftServerType.JAVA_EDITION)


@test
async def full_flow_bedrock(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config entry for a Bedrock Edition server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            return_value=BedrockServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.async_status",
            return_value=TEST_BEDROCK_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result["data"][CONF_TYPE]).to_equal(MinecraftServerType.BEDROCK_EDITION)


@test
async def full_flow_legacy_java(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config entry for a legacy Java Edition server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            return_value=LegacyServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_status",
            return_value=TEST_LEGACY_JAVA_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result["data"][CONF_TYPE]).to_equal(
            MinecraftServerType.LEGACY_JAVA_EDITION
        )


@test
async def service_already_configured_java(
    hass: HomeAssistant = Depends(hass_fixture),
    java_mock_config_entry: MockConfigEntry = Depends(java_mock_config_entry),
) -> None:
    """Test config flow abort if a Java Edition server is already configured."""
    java_mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            return_value=JavaServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_status",
            return_value=TEST_JAVA_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def service_already_configured_bedrock(
    hass: HomeAssistant = Depends(hass_fixture),
    bedrock_mock_config_entry: MockConfigEntry = Depends(bedrock_mock_config_entry),
) -> None:
    """Test config flow abort if a Bedrock Edition server is already configured."""
    bedrock_mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            return_value=BedrockServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.async_status",
            return_value=TEST_BEDROCK_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def service_already_configured_legacy_java(
    hass: HomeAssistant = Depends(hass_fixture),
    legacy_java_mock_config_entry: MockConfigEntry = Depends(
        legacy_java_mock_config_entry
    ),
) -> None:
    """Test config flow abort if a legacy Java Edition server is already configured."""
    legacy_java_mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            return_value=LegacyServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_status",
            return_value=TEST_LEGACY_JAVA_STATUS_RESPONSE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def recovery_java(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow recovery with a Java Edition server."""
    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            return_value=JavaServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_status",
            side_effect=OSError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            side_effect=ValueError,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            return_value=JavaServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_status",
            return_value=TEST_JAVA_STATUS_RESPONSE,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=USER_INPUT
        )
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result2["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result2["data"][CONF_TYPE]).to_equal(MinecraftServerType.JAVA_EDITION)


@test
async def recovery_bedrock(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow recovery with a Bedrock Edition server."""
    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            return_value=BedrockServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.async_status",
            side_effect=OSError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            side_effect=ValueError,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            return_value=BedrockServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.async_status",
            return_value=TEST_BEDROCK_STATUS_RESPONSE,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=USER_INPUT
        )
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result2["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result2["data"][CONF_TYPE]).to_equal(
            MinecraftServerType.BEDROCK_EDITION
        )


@test
async def recovery_legacy_java(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow recovery with a legacy Java Edition server."""
    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            return_value=LegacyServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_status",
            side_effect=OSError,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.minecraft_server.api.BedrockServer.lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=ValueError,
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_lookup",
            return_value=LegacyServer(host=TEST_HOST, port=TEST_PORT),
        ),
        patch(
            "homeassistant.components.minecraft_server.api.LegacyServer.async_status",
            return_value=TEST_LEGACY_JAVA_STATUS_RESPONSE,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=USER_INPUT
        )
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(USER_INPUT[CONF_ADDRESS])
        expect(result2["data"][CONF_ADDRESS]).to_equal(TEST_ADDRESS)
        expect(result2["data"][CONF_TYPE]).to_equal(
            MinecraftServerType.LEGACY_JAVA_EDITION
        )
