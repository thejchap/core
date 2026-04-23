"""Test the Namecheap DynamicDNS config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.namecheapdns.const import DOMAIN, UPDATE_URL
from homeassistant.components.namecheapdns.helpers import AuthFailed
from homeassistant.config_entries import (
    SOURCE_IMPORT,
    SOURCE_REAUTH,
    SOURCE_USER,
    ConfigEntryState,
)
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.namecheapdns._fixtures import (
    TEST_USER_INPUT,
    mock_config_entry,
    mock_namecheap,
    mock_setup_entry,
)
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
) -> None:
    """Wire fixtures into every test in this module."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    _mn: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home.example.com")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test.cases(
    test.case("unknown", ValueError, "unknown"),
    test.case("update_failed", False, "update_failed"),
    test.case("cannot_connect", ClientError, "cannot_connect"),
)
async def form_errors(
    side_effect: type[Exception] | bool,
    text_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    mock_namecheap_: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_namecheap_.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    mock_namecheap_.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home.example.com")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test
async def import_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
    _mn: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home.example.com")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)
    expect(
        issue_registry.async_get_issue(
            domain=HOMEASSISTANT_DOMAIN,
            issue_id=f"deprecated_yaml_{DOMAIN}",
        )
    ).to_be_truthy()


@test
async def import_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
    mock_namecheap_: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test import flow failed."""
    mock_namecheap_.side_effect = [False]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("update_failed")
    expect(len(mock_setup_entry_.mock_calls)).to_equal(0)
    expect(
        issue_registry.async_get_issue(
            domain=DOMAIN,
            issue_id="deprecated_yaml_import_issue_error",
        )
    ).to_be_truthy()


@test
async def init_import_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    _mn: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test yaml triggers import flow."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: TEST_USER_INPUT})
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mn: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("unknown", ValueError, "unknown"),
    test.case("update_failed", False, "update_failed"),
    test.case("cannot_connect", ClientError, "cannot_connect"),
    test.case("invalid_auth", AuthFailed, "invalid_auth"),
)
async def reconfigure_errors(
    side_effect: type[Exception] | bool,
    text_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_namecheap_: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test we handle errors during reconfigure."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_namecheap_.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    mock_namecheap_.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _mn: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test reauth flow."""
    aioclient_mock.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("unknown", ValueError, "unknown"),
    test.case("update_failed", False, "update_failed"),
    test.case("cannot_connect", ClientError, "cannot_connect"),
    test.case("invalid_auth", AuthFailed, "invalid_auth"),
)
async def reauth_errors(
    side_effect: type[Exception] | bool,
    text_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_namecheap_: AsyncMock = Depends(mock_namecheap),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test we handle errors during reauth."""
    aioclient_mock.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_namecheap_.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    mock_namecheap_.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def initiate_reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test authentication error initiates reauth flow."""
    aioclient_mock.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text=(
            "<interface-response><ErrCount>1</ErrCount><errors>"
            "<Err1>Passwords do not match</Err1></errors></interface-response>"
        ),
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)
    expect("context" in flow).to_be_truthy()
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(config_entry.entry_id)
