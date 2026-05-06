"""Test the Namecheap DynamicDNS config flow."""

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

from ._fixtures import (
    TEST_USER_INPUT,
    config_entry,
    mock_namecheap,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    issue_registry,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Trigger executor (module-level autouse) — only primes mock_network."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _namecheap: AsyncMock = Depends(mock_namecheap),
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

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("value_error", side_effect=ValueError, text_error="unknown"),
    test.case("update_failed", side_effect=False, text_error="update_failed"),
    test.case("client_error", side_effect=ClientError, text_error="cannot_connect"),
)
async def form_errors(
    side_effect: Exception | bool,
    text_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    namecheap: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    namecheap.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    namecheap.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home.example.com")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _namecheap: AsyncMock = Depends(mock_namecheap),
    issues: ir.IssueRegistry = Depends(issue_registry),
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
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(
        issues.async_get_issue(
            domain=HOMEASSISTANT_DOMAIN,
            issue_id=f"deprecated_yaml_{DOMAIN}",
        )
        is not None
    ).to_be(True)


@test
async def import_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    issues: ir.IssueRegistry = Depends(issue_registry),
    namecheap: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test import flow failed."""
    namecheap.side_effect = [False]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("update_failed")

    expect(len(setup_entry.mock_calls)).to_equal(0)

    expect(
        issues.async_get_issue(
            domain=DOMAIN,
            issue_id="deprecated_yaml_import_issue_error",
        )
        is not None
    ).to_be(True)


@test
async def init_import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _namecheap: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test yaml triggers import flow."""
    await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: TEST_USER_INPUT},
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _namecheap: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test reconfigure flow."""
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("value_error", side_effect=ValueError, text_error="unknown"),
    test.case("update_failed", side_effect=False, text_error="update_failed"),
    test.case("client_error", side_effect=ClientError, text_error="cannot_connect"),
    test.case("auth_failed", side_effect=AuthFailed, text_error="invalid_auth"),
)
async def reconfigure_errors(
    side_effect: Exception | bool,
    text_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    namecheap: AsyncMock = Depends(mock_namecheap),
) -> None:
    """Test we handle errors."""
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    namecheap.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    namecheap.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _namecheap: AsyncMock = Depends(mock_namecheap),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test reauth flow."""
    aioclient.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("value_error", side_effect=ValueError, text_error="unknown"),
    test.case("update_failed", side_effect=False, text_error="update_failed"),
    test.case("client_error", side_effect=ClientError, text_error="cannot_connect"),
    test.case("auth_failed", side_effect=AuthFailed, text_error="invalid_auth"),
)
async def reauth_errors(
    side_effect: Exception | bool,
    text_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    namecheap: AsyncMock = Depends(mock_namecheap),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we handle errors."""
    aioclient.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    namecheap.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": text_error})

    namecheap.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def initiate_reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test authentication error initiates reauth flow."""
    aioclient.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text=(
            "<interface-response><ErrCount>1</ErrCount><errors>"
            "<Err1>Passwords do not match</Err1></errors></interface-response>"
        ),
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)
