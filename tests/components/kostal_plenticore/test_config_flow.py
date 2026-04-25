"""Test the Kostal Plenticore Solar Inverter config flow."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

from pykoplenti import ApiClient, AuthenticationException, SettingsData
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.kostal_plenticore.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_apiclient, mock_apiclient_class, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_g1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    apiclient_class: type[ApiClient] = Depends(mock_apiclient_class),
    apiclient: ApiClient = Depends(mock_apiclient),
) -> None:
    """Test the config flow for G1 models."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.kostal_plenticore.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        apiclient.login = AsyncMock()
        apiclient.get_settings = AsyncMock(
            return_value={
                "scb:network": [
                    SettingsData(
                        min="1",
                        max="63",
                        default=None,
                        access="readwrite",
                        unit=None,
                        id="Hostname",
                        type="string",
                    ),
                ]
            }
        )
        apiclient.get_setting_values = AsyncMock(
            return_value={"scb:network": {"Hostname": "scb"}}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )
        await hass.async_block_till_done()

        apiclient_class.assert_called_once_with(ANY, "1.1.1.1")
        apiclient.__aenter__.assert_called_once()
        apiclient.__aexit__.assert_called_once()
        apiclient.login.assert_called_once_with("test-password", service_code=None)
        apiclient.get_settings.assert_called_once()
        apiclient.get_setting_values.assert_called_once_with(
            "scb:network", "Hostname"
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("scb")
    expect(result["data"]).to_equal(
        {"host": "1.1.1.1", "password": "test-password"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_g2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    apiclient_class: type[ApiClient] = Depends(mock_apiclient_class),
    apiclient: ApiClient = Depends(mock_apiclient),
) -> None:
    """Test the config flow for G2 models."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.kostal_plenticore.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        apiclient.login = AsyncMock()
        apiclient.get_settings = AsyncMock(
            return_value={
                "scb:network": [
                    SettingsData(
                        min="1",
                        max="63",
                        default=None,
                        access="readwrite",
                        unit=None,
                        id="Network:Hostname",
                        type="string",
                    ),
                ]
            }
        )
        apiclient.get_setting_values = AsyncMock(
            return_value={"scb:network": {"Network:Hostname": "scb"}}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )
        await hass.async_block_till_done()

        apiclient_class.assert_called_once_with(ANY, "1.1.1.1")
        apiclient.login.assert_called_once_with("test-password", service_code=None)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("scb")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_g2_with_service_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    apiclient_class: type[ApiClient] = Depends(mock_apiclient_class),
    apiclient: ApiClient = Depends(mock_apiclient),
) -> None:
    """Test the config flow for G2 models with a Service Code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.kostal_plenticore.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        apiclient.login = AsyncMock()
        apiclient.get_settings = AsyncMock(
            return_value={
                "scb:network": [
                    SettingsData(
                        min="1",
                        max="63",
                        default=None,
                        access="readwrite",
                        unit=None,
                        id="Network:Hostname",
                        type="string",
                    ),
                ]
            }
        )
        apiclient.get_setting_values = AsyncMock(
            return_value={"scb:network": {"Network:Hostname": "scb"}}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "password": "test-password",
                "service_code": "test-service-code",
            },
        )
        await hass.async_block_till_done()

        apiclient_class.assert_called_once_with(ANY, "1.1.1.1")
        apiclient.login.assert_called_once_with(
            "test-password", service_code="test-service-code"
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("scb")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


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
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(
            side_effect=AuthenticationException(404, "invalid user"),
        )

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"password": "invalid_auth"})


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
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(side_effect=TimeoutError())

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "cannot_connect"})


@test
async def form_unexpected_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(side_effect=Exception())

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle already configured error."""
    MockConfigEntry(
        domain="kostal_plenticore",
        data={"host": "1.1.1.1", "password": "foobar"},
        unique_id="112233445566",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "1.1.1.1", "password": "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    apiclient_class: type[ApiClient] = Depends(mock_apiclient_class),
    apiclient: ApiClient = Depends(mock_apiclient),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the config flow for G1 models."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({})

    apiclient.login = AsyncMock()
    apiclient.get_settings = AsyncMock(
        return_value={
            "scb:network": [
                SettingsData(
                    min="1",
                    max="63",
                    default=None,
                    access="readwrite",
                    unit=None,
                    id="Hostname",
                    type="string",
                ),
            ]
        }
    )
    apiclient.get_setting_values = AsyncMock(
        return_value={"scb:network": {"Hostname": "scb"}}
    )

    with patch(
        "homeassistant.components.kostal_plenticore.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )
        await hass.async_block_till_done()

    apiclient_class.assert_called_once_with(ANY, "1.1.1.1")

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("1.1.1.1")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("test-password")


@test
async def reconfigure_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle invalid auth while reconfiguring."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(
            side_effect=AuthenticationException(404, "invalid user"),
        )

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"password": "invalid_auth"})


@test
async def reconfigure_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle cannot connect error."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(side_effect=TimeoutError())

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"host": "cannot_connect"})


@test
async def reconfigure_unexpected_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle unexpected error."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient"
    ) as mock_api_class:
        mock_api_ctx = MagicMock()
        mock_api_ctx.login = AsyncMock(side_effect=Exception())

        mock_api = MagicMock()
        mock_api.__aenter__.return_value = mock_api_ctx
        mock_api.__aexit__.return_value = None

        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "password": "test-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def reconfigure_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle already configured error."""
    config_entry.add_to_hass(hass)
    MockConfigEntry(
        domain="kostal_plenticore",
        data={CONF_HOST: "1.1.1.1", CONF_PASSWORD: "foobar"},
        unique_id="112233445566",
    ).add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1", CONF_PASSWORD: "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
