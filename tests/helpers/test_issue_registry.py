"""Test the repairs websocket API."""

from functools import partial
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import async_capture_events, flush_store
from tests.hass_fixtures import hass, hass_storage, hass_unloaded, issue_registry


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def load_save_issues(hass: HomeAssistant = Depends(hass)) -> None:
    """Make sure that we can load/save data correctly."""
    issues = [
        {
            "breaks_in_ha_version": "2022.9",
            "domain": "test",
            "issue_id": "issue_1",
            "is_fixable": True,
            "is_persistent": False,
            "learn_more_url": "https://theuselessweb.com",
            "severity": "error",
            "translation_key": "abc_123",
            "translation_placeholders": {"abc": "123"},
        },
        {
            "breaks_in_ha_version": "2022.8",
            "domain": "test",
            "issue_id": "issue_2",
            "is_fixable": True,
            "is_persistent": False,
            "learn_more_url": "https://theuselessweb.com/abc",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "456"},
        },
        {
            "breaks_in_ha_version": "2022.7",
            "domain": "test",
            "issue_id": "issue_3",
            "is_fixable": True,
            "is_persistent": False,
            "learn_more_url": "https://checkboxrace.com",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "789"},
        },
        {
            "breaks_in_ha_version": "2022.6",
            "data": {"entry_id": "123"},
            "domain": "test",
            "issue_id": "issue_4",
            "is_fixable": True,
            "is_persistent": True,
            "learn_more_url": "https://checkboxrace.com/blah",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"xyz": "abc"},
        },
    ]

    await ir.async_load(hass)
    events = async_capture_events(hass, ir.EVENT_REPAIRS_ISSUE_REGISTRY_UPDATED)

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            is_fixable=issue["is_fixable"],
            is_persistent=issue["is_persistent"],
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await hass.async_block_till_done()

    expect(len(events)).to_equal(4)
    expect(events[0].data).to_equal(
        {"action": "create", "domain": "test", "issue_id": "issue_1"}
    )
    expect(events[1].data).to_equal(
        {"action": "create", "domain": "test", "issue_id": "issue_2"}
    )
    expect(events[2].data).to_equal(
        {"action": "create", "domain": "test", "issue_id": "issue_3"}
    )
    expect(events[3].data).to_equal(
        {"action": "create", "domain": "test", "issue_id": "issue_4"}
    )

    ir.async_ignore_issue(hass, issues[0]["domain"], issues[0]["issue_id"], True)
    await hass.async_block_till_done()

    expect(len(events)).to_equal(5)
    expect(events[4].data).to_equal(
        {"action": "update", "domain": "test", "issue_id": "issue_1"}
    )

    ir.async_create_issue(
        hass,
        issues[2]["domain"],
        issues[2]["issue_id"],
        breaks_in_ha_version=issues[2]["breaks_in_ha_version"],
        is_fixable=issues[2]["is_fixable"],
        is_persistent=issues[2]["is_persistent"],
        learn_more_url=issues[2]["learn_more_url"],
        severity=issues[2]["severity"],
        translation_key=issues[2]["translation_key"],
        translation_placeholders=issues[2]["translation_placeholders"],
    )
    await hass.async_block_till_done()

    expect(len(events)).to_equal(5)

    ir.async_create_issue(
        hass,
        issues[2]["domain"],
        issues[2]["issue_id"],
        breaks_in_ha_version=issues[2]["breaks_in_ha_version"],
        is_fixable=issues[2]["is_fixable"],
        is_persistent=issues[2]["is_persistent"],
        learn_more_url="https://www.example.com/something_changed",
        severity=issues[2]["severity"],
        translation_key=issues[2]["translation_key"],
        translation_placeholders=issues[2]["translation_placeholders"],
    )
    await hass.async_block_till_done()

    expect(len(events)).to_equal(6)
    expect(events[5].data).to_equal(
        {"action": "update", "domain": "test", "issue_id": "issue_3"}
    )

    ir.async_delete_issue(hass, issues[2]["domain"], issues[2]["issue_id"])
    await hass.async_block_till_done()

    expect(len(events)).to_equal(7)
    expect(events[6].data).to_equal(
        {"action": "remove", "domain": "test", "issue_id": "issue_3"}
    )

    registry = hass.data[ir.DATA_REGISTRY]
    expect(len(registry.issues)).to_equal(3)
    issue1 = registry.async_get_issue("test", "issue_1")
    issue2 = registry.async_get_issue("test", "issue_2")
    issue4 = registry.async_get_issue("test", "issue_4")

    registry2 = ir.IssueRegistry(hass)
    await flush_store(registry._store)
    await registry2.async_load()

    expect(list(registry.issues)).to_equal(list(registry2.issues))

    issue1_registry2 = registry2.async_get_issue("test", "issue_1")
    expect(issue1_registry2).to_equal(
        ir.IssueEntry(
            active=False,
            breaks_in_ha_version=None,
            created=issue1.created,
            data=None,
            dismissed_version=issue1.dismissed_version,
            domain=issue1.domain,
            is_fixable=None,
            is_persistent=issue1.is_persistent,
            issue_domain=None,
            issue_id=issue1.issue_id,
            learn_more_url=None,
            severity=None,
            translation_key=None,
            translation_placeholders=None,
        )
    )
    issue2_registry2 = registry2.async_get_issue("test", "issue_2")
    expect(issue2_registry2).to_equal(
        ir.IssueEntry(
            active=False,
            breaks_in_ha_version=None,
            created=issue2.created,
            data=None,
            dismissed_version=issue2.dismissed_version,
            domain=issue2.domain,
            is_fixable=None,
            is_persistent=issue2.is_persistent,
            issue_domain=None,
            issue_id=issue2.issue_id,
            learn_more_url=None,
            severity=None,
            translation_key=None,
            translation_placeholders=None,
        )
    )
    issue4_registry2 = registry2.async_get_issue("test", "issue_4")
    expect(issue4_registry2).to_equal(issue4)


@test
async def load_save_issues_read_only(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Make sure that we don't save data when opened in read-only mode."""
    hass_storage[ir.STORAGE_KEY] = {
        "version": ir.STORAGE_VERSION_MAJOR,
        "minor_version": ir.STORAGE_VERSION_MINOR,
        "data": {
            "issues": [
                {
                    "created": "2022-07-19T09:41:13.746514+00:00",
                    "dismissed_version": "2022.7.0.dev0",
                    "domain": "test",
                    "is_persistent": False,
                    "issue_id": "issue_1",
                },
            ]
        },
    }

    issues = [
        {
            "breaks_in_ha_version": "2022.8",
            "domain": "test",
            "issue_id": "issue_2",
            "is_fixable": True,
            "is_persistent": False,
            "learn_more_url": "https://theuselessweb.com/abc",
            "severity": "other",
            "translation_key": "even_worse",
            "translation_placeholders": {"def": "456"},
        },
    ]

    events = async_capture_events(hass, ir.EVENT_REPAIRS_ISSUE_REGISTRY_UPDATED)
    await ir.async_load(hass, read_only=True)

    for issue in issues:
        ir.async_create_issue(
            hass,
            issue["domain"],
            issue["issue_id"],
            breaks_in_ha_version=issue["breaks_in_ha_version"],
            is_fixable=issue["is_fixable"],
            is_persistent=issue["is_persistent"],
            learn_more_url=issue["learn_more_url"],
            severity=issue["severity"],
            translation_key=issue["translation_key"],
            translation_placeholders=issue["translation_placeholders"],
        )

    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal(
        {"action": "create", "domain": "test", "issue_id": "issue_2"}
    )

    registry = ir.async_get(hass)
    expect(len(registry.issues)).to_equal(2)

    registry2 = ir.IssueRegistry(hass)
    await flush_store(registry._store)
    await registry2.async_load()

    expect(len(registry2.issues)).to_equal(1)


@test
async def loading_issues_from_storage(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading stored issues on start."""
    hass_storage[ir.STORAGE_KEY] = {
        "version": ir.STORAGE_VERSION_MAJOR,
        "minor_version": ir.STORAGE_VERSION_MINOR,
        "data": {
            "issues": [
                {
                    "created": "2022-07-19T09:41:13.746514+00:00",
                    "dismissed_version": "2022.7.0.dev0",
                    "domain": "test",
                    "is_persistent": False,
                    "issue_id": "issue_1",
                },
                {
                    "created": "2022-07-19T19:41:13.746514+00:00",
                    "dismissed_version": None,
                    "domain": "test",
                    "is_persistent": False,
                    "issue_id": "issue_2",
                },
                {
                    "breaks_in_ha_version": "2022.6",
                    "created": "2022-07-19T19:41:13.746514+00:00",
                    "data": {"entry_id": "123"},
                    "dismissed_version": None,
                    "domain": "test",
                    "issue_domain": "blubb",
                    "issue_id": "issue_4",
                    "is_fixable": True,
                    "is_persistent": True,
                    "learn_more_url": "https://checkboxrace.com/blah",
                    "severity": "other",
                    "translation_key": "even_worse",
                    "translation_placeholders": {"xyz": "abc"},
                },
            ]
        },
    }

    await ir.async_load(hass)

    registry = hass.data[ir.DATA_REGISTRY]
    expect(len(registry.issues)).to_equal(3)


@test
async def migration_1_1(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migration from version 1.1."""
    hass_storage[ir.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "data": {
            "issues": [
                {
                    "created": "2022-07-19T09:41:13.746514+00:00",
                    "dismissed_version": "2022.7.0.dev0",
                    "domain": "test",
                    "issue_id": "issue_1",
                },
                {
                    "created": "2022-07-19T19:41:13.746514+00:00",
                    "dismissed_version": None,
                    "domain": "test",
                    "issue_id": "issue_2",
                },
            ]
        },
    }

    await ir.async_load(hass)

    registry = hass.data[ir.DATA_REGISTRY]
    expect(len(registry.issues)).to_equal(2)


@test
async def get_or_create_thread_safety(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test call async_get_or_create_from a thread."""
    try:
        await hass.async_add_executor_job(
            partial(
                ir.async_create_issue,
                hass,
                "any",
                "any",
                is_fixable=True,
                severity="error",
                translation_key="any",
            )
        )
    except RuntimeError as err:
        expect(
            "Detected code that calls issue_registry.async_get_or_create from a thread"
            in str(err)
        ).to_be(True)
    else:
        expect("raised RuntimeError").to_equal("no exception")


@test
async def async_delete_issue_thread_safety(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test call async_delete_issue from a thread."""
    ir.async_create_issue(
        hass,
        "any",
        "any",
        is_fixable=True,
        severity="error",
        translation_key="any",
    )

    try:
        await hass.async_add_executor_job(
            ir.async_delete_issue,
            hass,
            "any",
            "any",
        )
    except RuntimeError as err:
        expect(
            "Detected code that calls issue_registry.async_delete from a thread"
            in str(err)
        ).to_be(True)
    else:
        expect("raised RuntimeError").to_equal("no exception")


@test
async def async_ignore_issue_thread_safety(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test call async_ignore_issue from a thread."""
    ir.async_create_issue(
        hass,
        "any",
        "any",
        is_fixable=True,
        severity="error",
        translation_key="any",
    )

    try:
        await hass.async_add_executor_job(
            ir.async_ignore_issue, hass, "any", "any", True
        )
    except RuntimeError as err:
        expect(
            "Detected code that calls issue_registry.async_ignore from a thread"
            in str(err)
        ).to_be(True)
    else:
        expect("raised RuntimeError").to_equal("no exception")
