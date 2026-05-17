"""Test the repairs websocket API."""

from http import HTTPStatus
from typing import Any
from unittest.mock import ANY, AsyncMock, Mock

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.components.repairs.const import DOMAIN
from homeassistant.const import __version__ as ha_version
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import MockUser, mock_platform
from tests.hass_fixtures import (
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_client as hass_client_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import (
    ClientSessionGenerator,
    MockHAClientWebSocket,
    WebSocketGenerator,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


DEFAULT_ISSUES = [
    {
        "breaks_in_ha_version": "2022.9",
        "domain": "fake_integration",
        "issue_id": "issue_1",
        "is_fixable": True,
        "learn_more_url": "https://theuselessweb.com",
        "severity": "error",
        "translation_key": "abc_123",
        "translation_placeholders": {"abc": "123"},
    }
]


async def create_issues(
    hass: HomeAssistant,
    ws_client: MockHAClientWebSocket,
    issues: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Create issues."""

    def api_issue(issue):
        excluded_keys = ("data",)
        return dict(
            {key: issue[key] for key in issue if key not in excluded_keys},
            created=ANY,
            dismissed_version=None,
            ignored=False,
            issue_domain=None,
        )

    if issues is None:
        issues = DEFAULT_ISSUES

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            data=issue.get("data"),
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert msg["result"] == {"issues": [api_issue(issue) for issue in issues]}

    return issues


EXPECTED_DATA = {
    "issue_1": None,
    "issue_2": {"blah": "bleh"},
    "abort_issue1": None,
}


class MockFixFlow(RepairsFlow):
    """Handler for an issue fixing flow."""

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""

        assert self.issue_id in EXPECTED_DATA
        assert self.data == EXPECTED_DATA[self.issue_id]

        return await self.async_step_custom_step()

    async def async_step_custom_step(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle a custom_step step of a fix flow."""
        if user_input is not None:
            return self.async_create_entry(data={})

        return self.async_show_form(step_id="custom_step", data_schema=vol.Schema({}))


class MockFixFlowAbort(RepairsFlow):
    """Handler for an issue fixing flow that aborts."""

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""
        return self.async_abort(reason="not_given")


@fixture
async def mock_repairs_integration(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Mock a repairs integration."""
    hass.config.components.add("fake_integration")

    def async_create_fix_flow(
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> RepairsFlow:
        assert issue_id in EXPECTED_DATA
        assert data == EXPECTED_DATA[issue_id]

        if issue_id == "abort_issue1":
            return MockFixFlowAbort()
        return MockFixFlow()

    mock_platform(
        hass,
        "fake_integration.repairs",
        Mock(async_create_fix_flow=AsyncMock(wraps=async_create_fix_flow)),
    )
    mock_platform(
        hass,
        "integration_without_repairs.repairs",
        Mock(spec=[]),
    )


@test
async def dismiss_issue(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can dismiss an issue."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    client = await hass_ws_client(hass)

    issues = await create_issues(hass, client)

    await client.send_json(
        {
            "id": 2,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "no_such_issue",
            "ignore": True,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)

    await client.send_json(
        {
            "id": 3,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "issue_1",
            "ignore": True,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_be(None)

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "issues": [
                dict(
                    issue,
                    created=ANY,
                    dismissed_version=ha_version,
                    ignored=True,
                    issue_domain=None,
                )
                for issue in issues
            ]
        }
    )

    await client.send_json(
        {
            "id": 5,
            "type": "repairs/ignore_issue",
            "domain": "fake_integration",
            "issue_id": "issue_1",
            "ignore": False,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_be(None)

    await client.send_json({"id": 6, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "issues": [
                dict(
                    issue,
                    created=ANY,
                    dismissed_version=None,
                    ignored=False,
                    issue_domain=None,
                )
                for issue in issues
            ]
        }
    )


@test
async def fix_non_existing_issue(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test trying to fix an issue that doesn't exist."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    issues = await create_issues(hass, ws_client)

    url = "/api/repairs/issues/fix"
    resp = await client.post(
        url, json={"handler": "no_such_integration", "issue_id": "no_such_issue"}
    )

    expect(resp.status).not_.to_equal(HTTPStatus.OK)

    url = "/api/repairs/issues/fix"
    resp = await client.post(
        url, json={"handler": "fake_integration", "issue_id": "no_such_issue"}
    )

    expect(resp.status).not_.to_equal(HTTPStatus.OK)

    await ws_client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "issues": [
                dict(
                    issue,
                    created=ANY,
                    dismissed_version=None,
                    ignored=False,
                    issue_domain=None,
                )
                for issue in issues
            ]
        }
    )


@test.cases(
    test.case(
        "fake_integration_custom_step",
        domain="fake_integration",
        step="custom_step",
        description_placeholders=None,
    ),
    test.case(
        "fake_integration_default_handler",
        domain="fake_integration_default_handler",
        step="confirm",
        description_placeholders={"abc": "123"},
    ),
)
async def fix_issue(
    domain: str,
    step: str,
    description_placeholders: dict[str, str] | None,
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can fix an issue."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    issues = [
        {
            **DEFAULT_ISSUES[0],
            "data": {"blah": "bleh"},
            "domain": domain,
            "issue_id": "issue_2",
        }
    ]
    await create_issues(hass, ws_client, issues=issues)

    url = "/api/repairs/issues/fix"
    resp = await client.post(url, json={"handler": domain, "issue_id": "issue_2"})

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "data_schema": [],
            "description_placeholders": description_placeholders,
            "errors": None,
            "flow_id": ANY,
            "handler": domain,
            "last_step": None,
            "preview": None,
            "step_id": step,
            "type": "form",
        }
    )

    url = f"/api/repairs/issues/fix/{flow_id}"
    # Test we can get the status of the flow
    resp2 = await client.get(url)

    expect(resp2.status).to_equal(HTTPStatus.OK)
    data2 = await resp2.json()

    expect(data).to_equal(data2)

    resp = await client.post(url)

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "description": None,
            "description_placeholders": None,
            "flow_id": flow_id,
            "handler": domain,
            "type": "create_entry",
        }
    )

    await ws_client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"issues": []})


@test
async def fix_issue_unauth(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can't query the result if not authorized."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    hass_admin_user.groups = []

    client = await hass_client()

    url = "/api/repairs/issues/fix"
    resp = await client.post(
        url, json={"handler": "fake_integration", "issue_id": "issue_1"}
    )

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def get_progress_unauth(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can't fix an issue if not authorized."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await create_issues(hass, ws_client)

    url = "/api/repairs/issues/fix"
    resp = await client.post(
        url, json={"handler": "fake_integration", "issue_id": "issue_1"}
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()
    flow_id = data["flow_id"]

    hass_admin_user.groups = []

    url = f"/api/repairs/issues/fix/{flow_id}"
    # Test we can't get the status of the flow
    resp = await client.get(url)
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def step_unauth(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can't fix an issue if not authorized."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await create_issues(hass, ws_client)

    url = "/api/repairs/issues/fix"
    resp = await client.post(
        url, json={"handler": "fake_integration", "issue_id": "issue_1"}
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()
    flow_id = data["flow_id"]

    hass_admin_user.groups = []

    url = f"/api/repairs/issues/fix/{flow_id}"
    # Test we can't get the status of the flow
    resp = await client.post(url)
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def list_issues(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    freezer: Any = Depends(freezer_fx),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can list issues."""
    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    freezer.move_to("2022-07-19 07:53:05")

    # Add an inactive issue, this should not be exposed in the list
    hass_storage[ir.STORAGE_KEY] = {
        "version": ir.STORAGE_VERSION_MAJOR,
        "data": {
            "issues": [
                {
                    "created": "2022-07-19T09:41:13.746514+00:00",
                    "dismissed_version": None,
                    "domain": "test",
                    "is_persistent": False,
                    "issue_id": "issue_3_inactive",
                    "issue_domain": None,
                },
            ]
        },
    }

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"issues": []})

    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "domain": "test",
            "is_fixable": True,
            "issue_id": "issue_1",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com",
            "severity": "error",
            "translation_key": "abc_123",
            "translation_placeholders": {"abc": "123"},
        },
        {
            "breaks_in_ha_version": "2022.8",
            "domain": "test",
            "is_fixable": False,
            "issue_id": "issue_2",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com/abc",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "456"},
        },
    ]

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "issues": [
                dict(
                    issue,
                    created="2022-07-19T07:53:05+00:00",
                    dismissed_version=None,
                    ignored=False,
                )
                for issue in issues
            ]
        }
    )


@test
async def fix_issue_aborted(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can fix an issue."""
    expect(await async_setup_component(hass, "http", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await create_issues(
        hass,
        ws_client,
        issues=[
            {
                **DEFAULT_ISSUES[0],
                "domain": "fake_integration",
                "issue_id": "abort_issue1",
            }
        ],
    )

    await ws_client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(len(msg["result"]["issues"])).to_equal(1)

    first_issue = msg["result"]["issues"][0]

    expect(first_issue["domain"]).to_equal("fake_integration")
    expect(first_issue["issue_id"]).to_equal("abort_issue1")

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "fake_integration", "issue_id": "abort_issue1"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "abort",
            "flow_id": flow_id,
            "handler": "fake_integration",
            "reason": "not_given",
            "description_placeholders": None,
        }
    )

    await ws_client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(len(msg["result"]["issues"])).to_equal(1)
    expect(msg["result"]["issues"][0]).to_equal(first_issue)


@test
async def get_issue_data(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    freezer: Any = Depends(freezer_fx),
    _mock_repairs: None = Depends(mock_repairs_integration),
) -> None:
    """Test we can get issue data."""
    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    freezer.move_to("2022-07-19 07:53:05")

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "data": None,
            "domain": "test",
            "is_fixable": True,
            "issue_id": "issue_1",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com",
            "severity": "error",
            "translation_key": "abc_123",
            "translation_placeholders": {"abc": "123"},
        },
        {
            "breaks_in_ha_version": "2022.8",
            "data": {"key": "value"},
            "domain": "test",
            "is_fixable": False,
            "issue_id": "issue_2",
            "issue_domain": None,
            "learn_more_url": "https://theuselessweb.com/abc",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "456"},
        },
    ]

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            data=issue["data"],
            is_fixable=issue["is_fixable"],
            is_persistent=False,
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "issue_1"}
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"issue_data": None})

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "issue_2"}
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"issue_data": {"key": "value"}})

    await client.send_json_auto_id(
        {"type": "repairs/get_issue_data", "domain": "test", "issue_id": "unknown"}
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "unknown_issue",
            "message": "Issue 'unknown' not found",
        }
    )
