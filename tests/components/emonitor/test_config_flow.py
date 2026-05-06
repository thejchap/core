"""Test the SiteSage Emonitor config flow."""

from unittest.mock import MagicMock, patch

from aioemonitor.monitor import EmonitorNetwork, EmonitorStatus
import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.emonitor.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_SERVICE_INFO = DhcpServiceInfo(
    hostname="emonitor",
    ip="1.2.3.4",
    macaddress="aabbccddeeff",
)


def _mock_emonitor():
    return EmonitorStatus(
        MagicMock(), EmonitorNetwork("AABBCCDDEEFF", "1.2.3.4"), MagicMock()
    )


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
            return_value=_mock_emonitor(),
        ),
        patch(
            "homeassistant.components.emonitor.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Emonitor DDEEFF")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


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
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_HOST: "cannot_connect"})


@test
async def dhcp_can_confirm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery flow can confirm right away."""
    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "Emonitor DDEEFF",
        }
    )

    with patch(
        "homeassistant.components.emonitor.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Emonitor DDEEFF")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_fails_to_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery flow that fails to connect."""
    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        side_effect=aiohttp.ClientError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def dhcp_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery flow that fails to connect."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_unique_id_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating an entry where the unique_id already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
            return_value=_mock_emonitor(),
        ),
        patch(
            "homeassistant.components.emonitor.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
