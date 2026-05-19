"""Test the repairs websocket API."""

from typing import Any
from unittest.mock import AsyncMock, Mock

from awesomeversion.exceptions import AwesomeVersionStrategyException
from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.repairs import repairs_flow_manager
from homeassistant.components.repairs.const import DOMAIN
from homeassistant.components.repairs.issue_handler import (
    RepairsFlowManager,
    async_process_repairs_platforms,
)
from homeassistant.const import __version__ as ha_version
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import mock_platform
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def create_update_issue(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test creating and updating issues."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    with freeze_time("2022-07-19 07:53:05"):
        await client.send_json({"id": 1, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"issues": []})

        issues = [
            {
                "breaks_in_ha_version": "2022.9.0dev0",
                "domain": "test",
                "issue_id": "issue_1",
                "is_fixable": True,
                "learn_more_url": "https://theuselessweb.com",
                "severity": "error",
                "translation_key": "abc_123",
                "translation_placeholders": {"abc": "123"},
            },
            {
                "breaks_in_ha_version": "2022.8",
                "domain": "test",
                "issue_id": "issue_2",
                "is_fixable": False,
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
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_create_issue(
            hass,
            issues[0]["domain"],
            issues[0]["issue_id"],
            breaks_in_ha_version=issues[0]["breaks_in_ha_version"],
            is_fixable=issues[0]["is_fixable"],
            is_persistent=False,
            issue_domain="my_issue_domain",
            learn_more_url="blablabla",
            severity=issues[0]["severity"],
            translation_key=issues[0]["translation_key"],
            translation_placeholders=issues[0]["translation_placeholders"],
        )

        await client.send_json({"id": 3, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]["issues"][0]).to_equal(
            dict(
                issues[0],
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=None,
                ignored=False,
                learn_more_url="blablabla",
                issue_domain="my_issue_domain",
            )
        )


@test.cases(
    test.case("invalid_version", ha_version_value="2022.9.cat"),
    test.case("future_version", ha_version_value="In the future: 2023.1.1"),
)
async def create_issue_invalid_version(
    ha_version_value: str,
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test creating an issue with invalid breaks in version."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    client = await hass_ws_client(hass)

    issue = {
        "breaks_in_ha_version": ha_version_value,
        "domain": "test",
        "issue_id": "issue_1",
        "is_fixable": True,
        "learn_more_url": "https://theuselessweb.com",
        "severity": "error",
        "translation_key": "abc_123",
        "translation_placeholders": {"abc": "123"},
    }

    async with expect_raises_async(AwesomeVersionStrategyException):
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

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"issues": []})


@test
async def ignore_issue(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test ignoring issues."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    with freeze_time("2022-07-19 07:53:05"):
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
                "learn_more_url": "https://theuselessweb.com",
                "severity": "error",
                "translation_key": "abc_123",
                "translation_placeholders": {"abc": "123"},
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
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        async with expect_raises_async(KeyError):
            ir.async_ignore_issue(hass, issues[0]["domain"], "no_such_issue", True)

        await client.send_json({"id": 3, "type": "repairs/list_issues"})
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
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], True)

        await client.send_json({"id": 4, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal(
            {
                "issues": [
                    dict(
                        issue,
                        created="2022-07-19T07:53:05+00:00",
                        dismissed_version=ha_version,
                        ignored=True,
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], True)

        await client.send_json({"id": 5, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal(
            {
                "issues": [
                    dict(
                        issue,
                        created="2022-07-19T07:53:05+00:00",
                        dismissed_version=ha_version,
                        ignored=True,
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_create_issue(
            hass,
            issues[0]["domain"],
            issues[0]["issue_id"],
            breaks_in_ha_version=issues[0]["breaks_in_ha_version"],
            is_fixable=issues[0]["is_fixable"],
            is_persistent=False,
            learn_more_url="blablabla",
            severity=issues[0]["severity"],
            translation_key=issues[0]["translation_key"],
            translation_placeholders=issues[0]["translation_placeholders"],
        )

        await client.send_json({"id": 6, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]["issues"][0]).to_equal(
            dict(
                issues[0],
                created="2022-07-19T07:53:05+00:00",
                dismissed_version=ha_version,
                ignored=True,
                learn_more_url="blablabla",
                issue_domain=None,
            )
        )

        ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], False)

        await client.send_json({"id": 7, "type": "repairs/list_issues"})
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
                        learn_more_url="blablabla",
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )


@test
async def delete_issue(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test we can delete an issue."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    with freeze_time("2022-07-19 07:53:05") as frozen:
        issues = [
            {
                "breaks_in_ha_version": "2022.9",
                "domain": "fake_integration",
                "issue_id": "issue_1",
                "is_fixable": True,
                "learn_more_url": "https://theuselessweb.com",
                "severity": "error",
                "translation_key": "abc_123",
                "translation_placeholders": {"abc": "123"},
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

        await client.send_json({"id": 1, "type": "repairs/list_issues"})
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
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_delete_issue(hass, issues[0]["domain"], "no_such_issue")

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
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )

        ir.async_delete_issue(hass, issues[0]["domain"], issues[0]["issue_id"])

        await client.send_json({"id": 3, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"issues": []})

        ir.async_delete_issue(hass, issues[0]["domain"], issues[0]["issue_id"])

        await client.send_json({"id": 4, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"issues": []})

        frozen.move_to("2022-07-19 08:53:05")

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

        await client.send_json({"id": 5, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal(
            {
                "issues": [
                    dict(
                        issue,
                        created="2022-07-19T08:53:05+00:00",
                        dismissed_version=None,
                        ignored=False,
                        issue_domain=None,
                    )
                    for issue in issues
                ]
            }
        )


@test
async def non_compliant_platform(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test non-compliant platforms are not registered."""
    hass.config.components.add("fake_integration")
    hass.config.components.add("integration_without_repairs")
    mock_platform(
        hass,
        "fake_integration.repairs",
        Mock(async_create_fix_flow=AsyncMock(return_value=True)),
    )
    mock_platform(
        hass,
        "integration_without_repairs.repairs",
        Mock(spec=[]),
    )
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    await async_process_repairs_platforms(hass)

    expect(list(hass.data[DOMAIN]["platforms"].keys())).to_equal(["fake_integration"])


@test
async def sync_methods(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test sync method for creating and deleting an issue."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    # Connect the WS client before freezing time so auth tokens issued under
    # the real clock don't appear pre-expired against the frozen 2022 epoch.
    client = await hass_ws_client(hass)

    with freeze_time("2022-07-21 08:22:00"):
        await client.send_json({"id": 1, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"issues": []})

        def _create_issue() -> None:
            ir.create_issue(
                hass,
                "fake_integration",
                "sync_issue",
                breaks_in_ha_version="2022.9",
                is_fixable=True,
                is_persistent=False,
                learn_more_url="https://theuselessweb.com",
                severity=ir.IssueSeverity.ERROR,
                translation_key="abc_123",
                translation_placeholders={"abc": "123"},
            )

        await hass.async_add_executor_job(_create_issue)
        await client.send_json({"id": 2, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal(
            {
                "issues": [
                    {
                        "breaks_in_ha_version": "2022.9",
                        "created": "2022-07-21T08:22:00+00:00",
                        "dismissed_version": None,
                        "domain": "fake_integration",
                        "ignored": False,
                        "is_fixable": True,
                        "issue_id": "sync_issue",
                        "issue_domain": None,
                        "learn_more_url": "https://theuselessweb.com",
                        "severity": "error",
                        "translation_key": "abc_123",
                        "translation_placeholders": {"abc": "123"},
                    }
                ]
            }
        )

        await hass.async_add_executor_job(
            ir.delete_issue, hass, "fake_integration", "sync_issue"
        )
        await client.send_json({"id": 3, "type": "repairs/list_issues"})
        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(msg["result"]).to_equal({"issues": []})


@test
async def flow_manager_helper(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test accessing the repairs flow manager with the helper."""
    expect(repairs_flow_manager(hass)).to_be(None)

    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

    flow_manager = repairs_flow_manager(hass)
    expect(flow_manager).not_.to_be(None)
    expect(isinstance(flow_manager, RepairsFlowManager)).to_be(True)
