"""Test the Homeassistant repairs module."""

from typing import Any

from homeassistant import config_entries
from homeassistant.components.repairs import DOMAIN as REPAIRS_DOMAIN
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tryke import Depends, expect, fixture, test

from tests.common import MockConfigEntry
from tests.components.repairs import (
    async_process_repairs_platforms,
    process_repair_fix_flow,
    start_repair_fix_flow,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client as hass_client_fx,
    hass_storage as hass_storage_fx,
    issue_registry as issue_registry_fx,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def integration_not_found_confirm_step(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test the integration_not_found issue confirm step."""
    expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(
        await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    MockConfigEntry(domain="test1").add_to_hass(hass)
    expect(await async_setup_component(hass, "test1", {})).to_be(False)
    await hass.async_block_till_done()
    entry1 = MockConfigEntry(domain="test1")
    entry1.add_to_hass(hass)
    entry2 = MockConfigEntry(domain="test1")
    entry2.add_to_hass(hass)
    issue_id = "integration_not_found.test1"

    await async_process_repairs_platforms(hass)
    http_client = await hass_client()

    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.translation_placeholders).to_equal({"domain": "test1"})

    data = await start_repair_fix_flow(http_client, HOMEASSISTANT_DOMAIN, issue_id)

    flow_id = data["flow_id"]
    expect(data["step_id"]).to_equal("init")
    expect(data["description_placeholders"]).to_equal({"domain": "test1"})

    data = await process_repair_fix_flow(http_client, flow_id)

    expect(data["type"]).to_equal("menu")

    # Apply fix
    data = await process_repair_fix_flow(
        http_client, flow_id, json={"next_step_id": "confirm"}
    )

    expect(data["type"]).to_equal("create_entry")

    await hass.async_block_till_done()

    expect(hass.config_entries.async_get_entry(entry1.entry_id)).to_be_none()
    expect(hass.config_entries.async_get_entry(entry2.entry_id)).to_be_none()

    # Assert the issue is resolved
    expect(
        issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    ).to_be_falsy()


@test
async def integration_not_found_ignore_step(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test the integration_not_found issue ignore step."""
    expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(
        await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    MockConfigEntry(domain="test1").add_to_hass(hass)
    expect(await async_setup_component(hass, "test1", {})).to_be(False)
    await hass.async_block_till_done()
    entry1 = MockConfigEntry(domain="test1")
    entry1.add_to_hass(hass)
    issue_id = "integration_not_found.test1"

    await async_process_repairs_platforms(hass)
    http_client = await hass_client()

    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.translation_placeholders).to_equal({"domain": "test1"})

    data = await start_repair_fix_flow(http_client, HOMEASSISTANT_DOMAIN, issue_id)

    flow_id = data["flow_id"]
    expect(data["step_id"]).to_equal("init")
    expect(data["description_placeholders"]).to_equal({"domain": "test1"})

    # Show menu
    data = await process_repair_fix_flow(http_client, flow_id)

    expect(data["type"]).to_equal("menu")

    # Apply fix
    data = await process_repair_fix_flow(
        http_client, flow_id, json={"next_step_id": "ignore"}
    )

    expect(data["type"]).to_equal("abort")
    expect(data["reason"]).to_equal("issue_ignored")

    await hass.async_block_till_done()

    expect(hass.config_entries.async_get_entry(entry1.entry_id)).to_be_truthy()

    # Assert the issue is resolved
    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.dismissed_version).not_.to_be_none()


@test
async def orphaned_config_entry_confirm_step(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test the orphaned_config_entry issue confirm step."""
    expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(
        await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    await async_process_repairs_platforms(hass)
    http_client = await hass_client()

    entry = MockConfigEntry(domain="test_issued", source=config_entries.SOURCE_IGNORE)
    entry_valid = MockConfigEntry(domain="test_valid")
    issue_id = f"orphaned_ignored_entry.{entry.entry_id}"

    hass_storage[config_entries.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 5,
        "data": {
            "entries": [
                {
                    "created_at": entry.created_at.isoformat(),
                    "data": {},
                    "disabled_by": None,
                    "discovery_keys": {},
                    "domain": "test_issued",
                    "entry_id": entry.entry_id,
                    "minor_version": 1,
                    "modified_at": entry.modified_at.isoformat(),
                    "options": {},
                    "pref_disable_new_entities": False,
                    "pref_disable_polling": False,
                    "source": "ignore",
                    "subentries": [],
                    "title": "Title probably no-one will read",
                    "unique_id": None,
                    "version": 1,
                },
                {
                    "created_at": entry_valid.created_at.isoformat(),
                    "data": {},
                    "disabled_by": None,
                    "discovery_keys": {},
                    "domain": "test_valid",
                    "entry_id": entry_valid.entry_id,
                    "minor_version": 1,
                    "modified_at": entry_valid.modified_at.isoformat(),
                    "options": {},
                    "pref_disable_new_entities": False,
                    "pref_disable_polling": False,
                    "source": "user",
                    "subentries": [],
                    "title": "Title probably no-one will read",
                    "unique_id": None,
                    "version": 1,
                },
            ]
        },
    }

    await hass.config_entries.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.translation_placeholders).to_equal({"domain": "test_issued"})

    data = await start_repair_fix_flow(http_client, HOMEASSISTANT_DOMAIN, issue_id)

    flow_id = data["flow_id"]
    expect(data["step_id"]).to_equal("init")
    expect(data["description_placeholders"]).to_equal(
        {
            "entry_id": entry.entry_id,
            "domain": "test_issued",
        }
    )

    data = await process_repair_fix_flow(http_client, flow_id)

    expect(data["type"]).to_equal("menu")

    # Apply fix
    data = await process_repair_fix_flow(
        http_client, flow_id, json={"next_step_id": "confirm"}
    )

    expect(data["type"]).to_equal("create_entry")

    await hass.async_block_till_done()

    expect(hass.config_entries.async_get_entry(entry.entry_id)).to_be_none()
    expect(hass.config_entries.async_get_entry(entry_valid.entry_id)).not_.to_be_none()

    expect(
        issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    ).to_be_falsy()


@test
async def orphaned_config_entry_ignore_step(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test the orphaned_config_entry issue ignore step."""
    expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(
        await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    await async_process_repairs_platforms(hass)
    http_client = await hass_client()

    entry = MockConfigEntry(domain="test_issued", source=config_entries.SOURCE_IGNORE)
    entry_valid = MockConfigEntry(domain="test_valid")
    issue_id = f"orphaned_ignored_entry.{entry.entry_id}"

    hass_storage[config_entries.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 5,
        "data": {
            "entries": [
                {
                    "created_at": entry.created_at.isoformat(),
                    "data": {},
                    "disabled_by": None,
                    "discovery_keys": {},
                    "domain": "test_issued",
                    "entry_id": entry.entry_id,
                    "minor_version": 1,
                    "modified_at": entry.modified_at.isoformat(),
                    "options": {},
                    "pref_disable_new_entities": False,
                    "pref_disable_polling": False,
                    "source": "ignore",
                    "subentries": [],
                    "title": "Title probably no-one will read",
                    "unique_id": None,
                    "version": 1,
                },
                {
                    "created_at": entry_valid.created_at.isoformat(),
                    "data": {},
                    "disabled_by": None,
                    "discovery_keys": {},
                    "domain": "test_valid",
                    "entry_id": entry_valid.entry_id,
                    "minor_version": 1,
                    "modified_at": entry_valid.modified_at.isoformat(),
                    "options": {},
                    "pref_disable_new_entities": False,
                    "pref_disable_polling": False,
                    "source": "user",
                    "subentries": [],
                    "title": "Title probably no-one will read",
                    "unique_id": None,
                    "version": 1,
                },
            ]
        },
    }

    await hass.config_entries.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.translation_placeholders).to_equal({"domain": "test_issued"})

    data = await start_repair_fix_flow(http_client, HOMEASSISTANT_DOMAIN, issue_id)

    flow_id = data["flow_id"]
    expect(data["step_id"]).to_equal("init")
    expect(data["description_placeholders"]).to_equal(
        {
            "entry_id": entry.entry_id,
            "domain": "test_issued",
        }
    )

    data = await process_repair_fix_flow(http_client, flow_id)

    expect(data["type"]).to_equal("menu")

    # Apply fix
    data = await process_repair_fix_flow(
        http_client, flow_id, json={"next_step_id": "ignore"}
    )

    expect(data["type"]).to_equal("abort")
    expect(data["reason"]).to_equal("issue_ignored")

    await hass.async_block_till_done()

    expect(hass.config_entries.async_get_entry(entry.entry_id)).to_be_truthy()

    # Assert the issue is resolved
    issue = issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)
    expect(issue).not_.to_be_none()
    expect(issue.dismissed_version).not_.to_be_none()
