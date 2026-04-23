"""Tests for the Mealie config flow."""

from unittest.mock import AsyncMock

from aiomealie import About, MealieAuthenticationError, MealieConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.mealie.const import DOMAIN
from homeassistant.config_entries import SOURCE_HASSIO, SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_API_TOKEN, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from . import setup_integration
from ._fixtures import (
    mock_async_zeroconf,
    mock_config_entry,
    mock_mealie_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mzc: object = Depends(mock_async_zeroconf),
    _mmc: AsyncMock = Depends(mock_mealie_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Mealie")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "demo.mealie.io",
            CONF_API_TOKEN: "token",
            CONF_VERIFY_SSL: True,
        }
    )
    expect(result["result"].unique_id).to_equal("bf1c62fe-4941-4332-9886-e54e88dbdba0")


@test.cases(
    test.case("cannot_connect", MealieConnectionError, "cannot_connect"),
    test.case("invalid_auth", MealieAuthenticationError, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
) -> None:
    """Test flow errors."""
    mock_client.get_user_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def ingress_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
) -> None:
    """Test disallow ingress host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "http://homeassistant/app/db21ed7f_mealie",
            CONF_API_TOKEN: "token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "ingress_url"})

    mock_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://homeassistant:9001", CONF_API_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("beta_5", "v1.0.0beta-5"),
    test.case("rc2", "v1.0.0-RC2"),
    test.case("v0_1_0", "v0.1.0"),
    test.case("v1_9_0", "v1.9.0"),
    test.case("beta_2", "v2.0.0beta-2"),
)
async def flow_version_error(
    version: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
) -> None:
    """Test flow version error."""
    mock_client.get_about.return_value = About(version=version)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "mealie_version"})


@test
async def duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow."""
    await setup_integration(hass, entry)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "token2"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_API_TOKEN]).to_equal("token2")


@test
async def reauth_flow_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with wrong account."""
    await setup_integration(hass, entry)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_client.get_user_info.return_value.user_id = "wrong_user_id"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "token2"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test.cases(
    test.case("cannot_connect", MealieConnectionError, "cannot_connect"),
    test.case("invalid_auth", MealieAuthenticationError, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def reauth_flow_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow errors."""
    await setup_integration(hass, entry)
    mock_client.get_user_info.side_effect = exception

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    mock_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    await setup_integration(hass, entry)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "http://test:9090",
            CONF_API_TOKEN: "token2",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_API_TOKEN]).to_equal("token2")
    expect(entry.data[CONF_HOST]).to_equal("http://test:9090")
    expect(entry.data[CONF_VERIFY_SSL]).to_be(False)


@test
async def reconfigure_flow_wrong_account(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with wrong account."""
    await setup_integration(hass, entry)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_client.get_user_info.return_value.user_id = "wrong_user_id"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://test:9090", CONF_API_TOKEN: "token2"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test.cases(
    test.case("cannot_connect", MealieConnectionError, "cannot_connect"),
    test.case("invalid_auth", MealieAuthenticationError, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def reconfigure_flow_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow errors."""
    await setup_integration(hass, entry)
    mock_client.get_user_info.side_effect = exception

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://test:9090", CONF_API_TOKEN: "token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    mock_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://test:9090", CONF_API_TOKEN: "token"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def hassio_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test successful Supervisor flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={"addon": "Mealie", "host": "http://test", "port": 9090},
            name="mealie",
            slug="mealie",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("hassio_confirm")
    expect(result.get("description_placeholders")).to_equal({"addon": "Mealie"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Mealie")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "http://test:9090",
            CONF_API_TOKEN: "token",
            CONF_VERIFY_SSL: True,
        }
    )
    expect(result["result"].unique_id).to_equal("bf1c62fe-4941-4332-9886-e54e88dbdba0")


@test
async def hassio_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we only allow a single config flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={
                "addon": "Mealie",
                "host": "mock-mealie",
                "port": "9090",
            },
            name="Mealie",
            slug="mealie",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )
    expect(result).not_.to_be(None)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def hassio_ignored(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the supervisor discovered instance can be ignored."""
    MockConfigEntry(domain=DOMAIN, source=SOURCE_IGNORE).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={
                "addon": "Mealie",
                "host": "mock-mealie",
                "port": "9090",
            },
            name="Mealie",
            slug="mealie",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )
    expect(result).not_.to_be(None)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("cannot_connect", MealieConnectionError, "cannot_connect"),
    test.case("invalid_auth", MealieAuthenticationError, "invalid_auth"),
    test.case("unknown", Exception, "unknown"),
)
async def hassio_connection_error(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_mealie_client),
) -> None:
    """Test flow errors."""
    mock_client.get_user_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={"addon": "Mealie", "host": "http://test", "port": 9090},
            name="mealie",
            slug="mealie",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")
    expect(result["description_placeholders"]).to_equal({"addon": "Mealie"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
