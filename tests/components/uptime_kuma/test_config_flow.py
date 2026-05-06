"""Test the Uptime Kuma config flow."""

from unittest.mock import AsyncMock

from pythonkuma import (
    UptimeKumaAuthenticationException,
    UptimeKumaConnectionException,
    UptimeKumaParseException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.uptime_kuma.const import DOMAIN
from homeassistant.config_entries import SOURCE_HASSIO, SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_pythonkuma,
    mock_setup_entry,
    mock_update_checker,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ADDON_SERVICE_INFO = HassioServiceInfo(
    config={
        "addon": "Uptime Kuma",
        CONF_URL: "http://localhost:3001/",
    },
    name="Uptime Kuma",
    slug="a0d7b954_uptime-kuma",
    uuid="1234",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _update: AsyncMock = Depends(mock_update_checker),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("uptime.example.org")
    expect(dict(result["data"])).to_equal(
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=UptimeKumaConnectionException,
        text_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        raise_error=UptimeKumaAuthenticationException,
        text_error="invalid_auth",
    ),
    test.case(
        "invalid_data",
        raise_error=UptimeKumaParseException,
        text_error="invalid_data",
    ),
    test.case("unknown", raise_error=ValueError, text_error="unknown"),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test we handle errors and recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    kuma.metrics.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    kuma.metrics.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("uptime.example.org")
    expect(dict(result["data"])).to_equal(
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test we abort when entry is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "newapikey"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("newapikey")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=UptimeKumaConnectionException,
        text_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        raise_error=UptimeKumaAuthenticationException,
        text_error="invalid_auth",
    ),
    test.case(
        "invalid_data",
        raise_error=UptimeKumaParseException,
        text_error="invalid_data",
    ),
    test.case("unknown", raise_error=ValueError, text_error="unknown"),
)
async def flow_reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reauth flow errors and recover."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    kuma.metrics.side_effect = raise_error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "newapikey"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    kuma.metrics.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "newapikey"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("newapikey")

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        }
    )

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=UptimeKumaConnectionException,
        text_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        raise_error=UptimeKumaAuthenticationException,
        text_error="invalid_auth",
    ),
    test.case(
        "invalid_data",
        raise_error=UptimeKumaParseException,
        text_error="invalid_data",
    ),
    test.case("unknown", raise_error=ValueError, text_error="unknown"),
)
async def flow_reconfigure_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reconfigure flow errors and recover."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    kuma.metrics.side_effect = raise_error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    kuma.metrics.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        }
    )

    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def hassio_addon_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test config flow initiated by Supervisor."""
    kuma.metrics.side_effect = [UptimeKumaAuthenticationException, None]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")
    expect(result["description_placeholders"]).to_equal({"addon": "Uptime Kuma"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "apikey"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("a0d7b954_uptime-kuma")
    expect(dict(result["data"])).to_equal(
        {
            CONF_URL: "http://localhost:3001/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_addon_discovery_confirm_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test config flow initiated by Supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")
    expect(result["description_placeholders"]).to_equal({"addon": "Uptime Kuma"})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("a0d7b954_uptime-kuma")
    expect(dict(result["data"])).to_equal(
        {
            CONF_URL: "http://localhost:3001/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: None,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_addon_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test config flow initiated by Supervisor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://localhost:3001/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "cannot_connect",
        raise_error=UptimeKumaConnectionException,
        text_error="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        raise_error=UptimeKumaAuthenticationException,
        text_error="invalid_auth",
    ),
    test.case(
        "invalid_data",
        raise_error=UptimeKumaParseException,
        text_error="invalid_data",
    ),
    test.case("unknown", raise_error=ValueError, text_error="unknown"),
)
async def hassio_addon_discovery_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    kuma: AsyncMock = Depends(mock_pythonkuma),
    *,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test we handle errors and recover."""
    kuma.metrics.side_effect = UptimeKumaAuthenticationException
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    kuma.metrics.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "apikey"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    kuma.metrics.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "apikey"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("a0d7b954_uptime-kuma")
    expect(dict(result["data"])).to_equal(
        {
            CONF_URL: "http://localhost:3001/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def hassio_addon_discovery_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test we abort discovery flow if discovery was ignored."""
    MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_IGNORE,
        data={},
        entry_id="123456789",
        unique_id="1234",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def hassio_addon_discovery_update_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _kuma: AsyncMock = Depends(mock_pythonkuma),
) -> None:
    """Test we abort if already configured and update from discovery info."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="a0d7b954_uptime-kuma",
        data={
            CONF_URL: "http://localhost:80/",
            CONF_VERIFY_SSL: True,
            CONF_API_KEY: "apikey",
        },
        entry_id="123456789",
        unique_id="1234",
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data[CONF_URL]).to_equal("http://localhost:3001/")
