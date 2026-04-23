"""Test the Duck DNS config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.duckdns import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DOMAIN
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.duckdns._fixtures import (
    NEW_TOKEN,
    TEST_SUBDOMAIN,
    TEST_TOKEN,
    config_entry,
    mock_setup_entry,
    mock_update_duckdns,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, issue_registry, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: "123e4567-e89b-12d3-a456-426614174000",
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"{TEST_SUBDOMAIN}.duckdns.org")
    expect(result["data"]).to_equal(
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we abort if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: "123e4567-e89b-12d3-a456-426614174000",
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("unknown", [ValueError, True], "unknown"),
    test.case("update_failed", [False, True], "update_failed"),
)
async def form_errors(
    side_effect: list[type[Exception] | bool],
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    mock_update_duckdns.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": text_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"{TEST_SUBDOMAIN}.duckdns.org")
    expect(result["data"]).to_equal(
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def _import(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test import flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"{TEST_SUBDOMAIN}.duckdns.org")
    expect(result["data"]).to_equal(
        {
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(
        issue_registry.async_get_issue(
            domain=HOMEASSISTANT_DOMAIN,
            issue_id=f"deprecated_yaml_{DOMAIN}",
        )
        is not None
    ).to_be(True)


@test
async def import_failed(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
    mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
) -> None:
    """Test import flow failed."""
    mock_update_duckdns.return_value = False
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("update_failed")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)

    expect(
        issue_registry.async_get_issue(
            domain=DOMAIN,
            issue_id="deprecated_yaml_import_issue_error",
        )
        is not None
    ).to_be(True)


@test
async def import_exception(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
    mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
) -> None:
    """Test import flow failed unknown."""
    mock_update_duckdns.side_effect = ValueError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_DOMAIN: TEST_SUBDOMAIN,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unknown")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)

    expect(
        issue_registry.async_get_issue(
            domain=DOMAIN,
            issue_id="deprecated_yaml_import_issue_error",
        )
        is not None
    ).to_be(True)


@test
async def init_import_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test yaml triggers import flow."""

    await async_setup_component(
        hass,
        DOMAIN,
        {"duckdns": {CONF_DOMAIN: TEST_SUBDOMAIN, CONF_ACCESS_TOKEN: TEST_TOKEN}},
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def flow_reconfigure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reconfigure flow."""

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_ACCESS_TOKEN]).to_equal(NEW_TOKEN)


@test.cases(
    test.case("unknown", [ValueError, True], "unknown"),
    test.case("update_failed", [False, True], "update_failed"),
)
async def flow_reconfigure_errors(
    side_effect: list[type[Exception] | bool],
    text_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_update_duckdns: AsyncMock = Depends(mock_update_duckdns),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test we handle errors."""

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_update_duckdns.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": text_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_ACCESS_TOKEN]).to_equal(NEW_TOKEN)
