"""Test the Balboa Spa Client config flow."""

from unittest.mock import MagicMock, patch

from pybalboa.exceptions import SpaConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.balboa.const import CONF_SYNC_TIME, DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.balboa._fixtures import client
from tests.hass_fixtures import hass, mock_network

TEST_HOST = "1.1.1.1"
TEST_DATA = {CONF_HOST: TEST_HOST}
TEST_MAC = "ef:ef:ef:c0:ff:ee"
TEST_DHCP_SERVICE_INFO = DhcpServiceInfo(
    ip=TEST_HOST, macaddress=TEST_MAC.replace(":", ""), hostname="fakespa"
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
            return_value=client,
        ),
        patch(
            "homeassistant.components.balboa.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["data"]).to_equal(TEST_DATA)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
        side_effect=SpaConnectionError(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_spa_not_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test we handle spa not configured error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
    ):
        client.async_configuration_loaded.return_value = False
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
        side_effect=Exception("Boom"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_DATA,
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test when provided credentials are already configured."""
    MockConfigEntry(domain=DOMAIN, data=TEST_DATA, unique_id=TEST_MAC).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
            return_value=client,
        ),
        patch(
            "homeassistant.components.balboa.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test specifying non default settings using options flow."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_DATA, unique_id=TEST_MAC)
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    with patch(
        "homeassistant.components.balboa.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_SYNC_TIME: True},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(dict(config_entry.options)).to_equal({CONF_SYNC_TIME: True})


@test
async def dhcp_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test we can process the discovery from dhcp."""
    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("FakeSpa")
        expect(result["data"]).to_equal(TEST_DATA)
        expect(result["result"].unique_id).to_equal(TEST_MAC)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery_updates_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test dhcp discovery updates host and aborts."""
    entry = MockConfigEntry(domain=DOMAIN, data=TEST_DATA, unique_id=TEST_MAC)
    entry.add_to_hass(hass)

    updated_ip = "1.1.1.2"
    TEST_DHCP_SERVICE_INFO.ip = updated_ip
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=TEST_DHCP_SERVICE_INFO,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data[CONF_HOST]).to_equal(updated_ip)


@test.cases(
    test.case("cannot_connect", SpaConnectionError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def dhcp_discovery_failed(
    side_effect: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test failed setup from dhcp."""
    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
        side_effect=side_effect(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal(reason)


@test
async def dhcp_discovery_manual_user_setup(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    client: MagicMock = Depends(client),
) -> None:
    """Test dhcp discovery with manual user setup."""
    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["data"]).to_equal(TEST_DATA)
