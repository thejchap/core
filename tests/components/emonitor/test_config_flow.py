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
from tests.components.emonitor._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network

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
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Emonitor DDEEFF")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
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

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
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

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({CONF_HOST: "cannot_connect"})


@test
async def dhcp_can_confirm(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {"host": "1.2.3.4", "name": "Emonitor DDEEFF"}
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

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Emonitor DDEEFF")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_fails_to_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def dhcp_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test DHCP discovery flow when entry already exists."""
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

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_unique_id_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
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
    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")
