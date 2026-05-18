"""Test supervisor repairs."""

from collections.abc import Generator
from dataclasses import replace
from http import HTTPStatus
import os
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

from aiohasupervisor import SupervisorError
from aiohasupervisor.models import (
    AddonsStats,
    AddonState,
    Check,
    CheckType,
    ContextType,
    InstalledAddonComplete,
    Issue,
    IssueType,
    ResolutionInfo,
    Suggestion,
    SuggestionType,
    UnhealthyReason,
    UnsupportedReason,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tryke import Depends, expect, fixture, test

from ._fixtures import (
    addon_changelog,
    addon_installed,
    addon_stats,
    addons_list,
    homeassistant_info,
    homeassistant_stats,
    host_info,
    ingress_panels,
    jobs_info,
    network_info,
    os_info,
    store_info,
    supervisor_client,
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
)

from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    issue_registry as issue_registry_fx,
    mock_network,
)

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def fixture_supervisor_environ() -> Generator[None]:
    """Mock os environ for supervisor."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        yield


def _mock_resolution_info(
    supervisor_client: AsyncMock,
    unsupported: list[UnsupportedReason] | None = None,
    unhealthy: list[UnhealthyReason] | None = None,
    issues: list[Issue] | None = None,
    suggestions_by_issue: dict[UUID, list[Suggestion]] | None = None,
    suggestion_result: SupervisorError | None = None,
) -> None:
    """Mock resolution/info endpoint with unsupported/unhealthy reasons and/or issues."""
    supervisor_client.resolution.info.return_value = ResolutionInfo(
        unsupported=unsupported or [],
        unhealthy=unhealthy or [],
        issues=issues or [],
        suggestions=[
            suggestion
            for issue_list in suggestions_by_issue.values()
            for suggestion in issue_list
        ]
        if suggestions_by_issue
        else [],
        checks=[
            Check(enabled=True, slug=CheckType.DOCKER_CONFIG),
            Check(enabled=True, slug=CheckType.FREE_SPACE),
        ],
    )

    if suggestions_by_issue:

        async def mock_suggestions_for_issue(uuid: UUID) -> list[Suggestion]:
            """Mock of suggestions for issue api."""
            return suggestions_by_issue.get(uuid, [])

        supervisor_client.resolution.suggestions_for_issue.side_effect = (
            mock_suggestions_for_issue
        )
        supervisor_client.resolution.apply_suggestion.side_effect = suggestion_result


def _apply_setup_mocks(
    addon_installed: AsyncMock,
    addon_stats: AsyncMock,
    addons_list: AsyncMock,
    *,
    include_addons: bool = False,
) -> None:
    """Apply the all_setup_requests behavior."""
    if include_addons:
        addons_list.return_value[0] = replace(
            addons_list.return_value[0],
            version="1.0.0",
            version_latest="1.0.0",
            update_available=False,
        )
        addons_list.return_value[1] = replace(
            addons_list.return_value[1],
            version="1.0.0",
            version_latest="1.0.0",
            state=AddonState.STARTED,
        )
    else:
        addons_list.return_value = []

    addon_installed.return_value.update_available = False
    addon_installed.return_value.version = "1.0.0"
    addon_installed.return_value.version_latest = "1.0.0"
    addon_installed.return_value.repository = "core"
    addon_installed.return_value.state = AddonState.STARTED
    addon_installed.return_value.icon = False

    def mock_addon_info(slug: str) -> Mock:
        addon = Mock(
            spec=InstalledAddonComplete,
            to_dict=addon_installed.return_value.to_dict,
            **addon_installed.return_value.to_dict(),
        )
        if slug == "test":
            addon.name = "test"
            addon.slug = "test"
            addon.url = "https://github.com/home-assistant/addons/test"
            addon.auto_update = True
        else:
            addon.name = "test2"
            addon.slug = "test2"
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info

    async def mock_addon_stats(addon: str) -> AddonsStats:
        """Mock addon stats for test and test2."""
        if addon == "test2":
            return AddonsStats(
                cpu_percent=0.8,
                memory_usage=51941376,
                memory_limit=3977146368,
                memory_percent=1.31,
                network_rx=31338284,
                network_tx=15692900,
                blk_read=740077568,
                blk_write=6004736,
            )
        return AddonsStats(
            cpu_percent=0.99,
            memory_usage=182611968,
            memory_limit=3977146368,
            memory_percent=4.59,
            network_rx=362570232,
            network_tx=82374138,
            blk_read=46010945536,
            blk_write=15051526144,
        )

    addon_stats.side_effect = mock_addon_stats


@fixture
def all_setup_requests(
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    addon_stats: AsyncMock = Depends(addon_stats),
    _jobs_info: AsyncMock = Depends(jobs_info),
    _host_info: AsyncMock = Depends(host_info),
    _supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    _homeassistant_info: AsyncMock = Depends(homeassistant_info),
    _supervisor_info: AsyncMock = Depends(supervisor_info),
    addons_list: AsyncMock = Depends(addons_list),
    _network_info: AsyncMock = Depends(network_info),
    _os_info: AsyncMock = Depends(os_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    """Mock all setup requests (default: without addons)."""
    _apply_setup_mocks(addon_installed, addon_stats, addons_list, include_addons=False)
    return addon_installed, addon_stats, addons_list


def _enable_addons(setup: tuple[AsyncMock, AsyncMock, AsyncMock]) -> None:
    """Switch all_setup_requests to include_addons=True for this test."""
    addon_installed, addon_stats, addons_list = setup
    # Re-create the addons_list since the default fixture wipes it to empty.
    from aiohasupervisor.models import (  # noqa: PLC0415
        AddonStage as _AddonStage,
        InstalledAddon as _InstalledAddon,
    )

    addons_list.return_value = [
        _InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test",
            repository="core",
            slug="test",
            stage=_AddonStage.STABLE,
            update_available=True,
            url="https://github.com/home-assistant/addons/test",
            version_latest="2.0.1",
            version="2.0.0",
            state=AddonState.STARTED,
        ),
        _InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test2",
            repository="core",
            slug="test2",
            stage=_AddonStage.STABLE,
            update_available=False,
            url="https://github.com",
            version_latest="3.1.0",
            version="3.1.0",
            state=AddonState.STOPPED,
        ),
    ]
    _apply_setup_mocks(addon_installed, addon_stats, addons_list, include_addons=True)


@test
async def supervisor_issue_repair_flow(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MULTIPLE_DATA_DISKS,
                context=ContextType.SYSTEM,
                reference="/dev/sda1",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.RENAME_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
                    uuid=sugg_uuid,
                    auto=False,
                )
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_rename_data_disk",
            "data_schema": [],
            "errors": None,
            "description_placeholders": {"reference": "/dev/sda1"},
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_repair_flow_with_multiple_suggestions(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue with multiple suggestions."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference="test",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference="test",
                    uuid=uuid4(),
                    auto=False,
                ),
                Suggestion(
                    type="test_type",
                    context=ContextType.SYSTEM,
                    reference="test",
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "menu",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "fix_menu",
            "data_schema": [
                {
                    "type": "select",
                    "options": [
                        ["system_execute_reboot", "system_execute_reboot"],
                        ["system_test_type", "system_test_type"],
                    ],
                    "required": False,
                    "name": "next_step_id",
                }
            ],
            "menu_options": ["system_execute_reboot", "system_test_type"],
            "description_placeholders": {"reference": "test"},
        }
    )

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}", json={"next_step_id": "system_test_type"}
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_repair_flow_with_multiple_suggestions_and_confirmation(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue with multiple suggestions and choice requires confirmation."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=sugg_uuid,
                    auto=False,
                ),
                Suggestion(
                    type="test_type",
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=uuid4(),
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "menu",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "fix_menu",
            "data_schema": [
                {
                    "type": "select",
                    "options": [
                        ["system_execute_reboot", "system_execute_reboot"],
                        ["system_test_type", "system_test_type"],
                    ],
                    "required": False,
                    "name": "next_step_id",
                }
            ],
            "menu_options": ["system_execute_reboot", "system_test_type"],
            "description_placeholders": None,
        }
    )

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "system_execute_reboot"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_execute_reboot",
            "data_schema": [],
            "errors": None,
            "description_placeholders": None,
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_repair_flow_skip_confirmation(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test confirmation skipped for fix flow for supervisor issue with one suggestion."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_execute_reboot",
            "data_schema": [],
            "errors": None,
            "description_placeholders": None,
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_ntp_sync_failed_repair_flow(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for NTP sync failed supervisor issue."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.NTP_SYNC_FAILED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.ENABLE_NTP,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_enable_ntp",
            "data_schema": [],
            "errors": None,
            "description_placeholders": None,
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_ntp_sync_failed_repair_flow_error(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow aborts when NTP re-enable fails."""
    issue_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.NTP_SYNC_FAILED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.ENABLE_NTP,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=uuid4(),
                    auto=False,
                ),
            ]
        },
        suggestion_result=SupervisorError("boom"),
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()
    flow_id = data["flow_id"]

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "abort",
            "flow_id": flow_id,
            "handler": "hassio",
            "reason": "apply_suggestion_fail",
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_truthy()


@test
async def mount_failed_repair_flow_error(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test repair flow fails when repair fails to apply."""
    issue_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MOUNT_FAILED,
                context=ContextType.MOUNT,
                reference="backup_share",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_RELOAD,
                    context=ContextType.MOUNT,
                    reference="backup_share",
                    uuid=uuid4(),
                    auto=False,
                ),
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.MOUNT,
                    reference="backup_share",
                    uuid=uuid4(),
                    auto=False,
                ),
            ]
        },
        suggestion_result=SupervisorError("boom"),
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()
    flow_id = data["flow_id"]

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "mount_execute_reload"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "abort",
            "flow_id": flow_id,
            "handler": "hassio",
            "reason": "apply_suggestion_fail",
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_truthy()


@test
async def mount_failed_repair_flow(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test repair flow for mount_failed issue."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MOUNT_FAILED,
                context=ContextType.MOUNT,
                reference="backup_share",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_RELOAD,
                    context=ContextType.MOUNT,
                    reference="backup_share",
                    uuid=sugg_uuid,
                    auto=False,
                ),
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.MOUNT,
                    reference="backup_share",
                    uuid=uuid4(),
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "menu",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "fix_menu",
            "data_schema": [
                {
                    "type": "select",
                    "options": [
                        ["mount_execute_reload", "mount_execute_reload"],
                        ["mount_execute_remove", "mount_execute_remove"],
                    ],
                    "required": False,
                    "name": "next_step_id",
                }
            ],
            "menu_options": ["mount_execute_reload", "mount_execute_remove"],
            "description_placeholders": {
                "reference": "backup_share",
                "storage_url": "/config/storage",
            },
        }
    )

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "mount_execute_reload"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_docker_config_repair_flow(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue."""
    _enable_addons(_setup)
    issue1_uuid = uuid4()
    issue2_uuid = uuid4()
    issue3_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.DOCKER_CONFIG,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=issue1_uuid,
            ),
            Issue(
                type=IssueType.DOCKER_CONFIG,
                context=ContextType.CORE,
                reference=None,
                uuid=issue2_uuid,
            ),
            Issue(
                type=IssueType.DOCKER_CONFIG,
                context=ContextType.ADDON,
                reference="test",
                uuid=issue3_uuid,
            ),
        ],
        suggestions_by_issue={
            issue1_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBUILD,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ],
            issue2_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBUILD,
                    context=ContextType.CORE,
                    reference=None,
                    uuid=uuid4(),
                    auto=False,
                ),
            ],
            issue3_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBUILD,
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=uuid4(),
                    auto=False,
                ),
            ],
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue1_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_execute_rebuild",
            "data_schema": [],
            "errors": None,
            "description_placeholders": {"components": "Home Assistant\n- test"},
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue1_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_repair_flow_multiple_data_disks(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for multiple data disks supervisor issue."""
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MULTIPLE_DATA_DISKS,
                context=ContextType.SYSTEM,
                reference="/dev/sda1",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.RENAME_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
                    uuid=uuid4(),
                    auto=False,
                ),
                Suggestion(
                    type=SuggestionType.ADOPT_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "menu",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "fix_menu",
            "data_schema": [
                {
                    "type": "select",
                    "options": [
                        ["system_rename_data_disk", "system_rename_data_disk"],
                        ["system_adopt_data_disk", "system_adopt_data_disk"],
                    ],
                    "required": False,
                    "name": "next_step_id",
                }
            ],
            "menu_options": ["system_rename_data_disk", "system_adopt_data_disk"],
            "description_placeholders": {"reference": "/dev/sda1"},
        }
    )

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "system_adopt_data_disk"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "system_adopt_data_disk",
            "data_schema": [],
            "errors": None,
            "description_placeholders": {"reference": "/dev/sda1"},
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_detached_addon_removed(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue."""
    _enable_addons(_setup)
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.DETACHED_ADDON_REMOVED,
                context=ContextType.ADDON,
                reference="test",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "addon_execute_remove",
            "data_schema": [],
            "errors": None,
            "description_placeholders": {
                "reference": "test",
                "addon": "test",
                "help_url": "https://www.home-assistant.io/help/",
                "community_url": "https://community.home-assistant.io/",
            },
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


@test
async def supervisor_issue_addon_boot_fail(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue."""
    _enable_addons(_setup)
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type="boot_fail",
                context=ContextType.ADDON,
                reference="test",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type="execute_start",
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=sugg_uuid,
                    auto=False,
                ),
                Suggestion(
                    type="disable_boot",
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=uuid4(),
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "menu",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "fix_menu",
            "data_schema": [
                {
                    "type": "select",
                    "options": [
                        ["addon_execute_start", "addon_execute_start"],
                        ["addon_disable_boot", "addon_disable_boot"],
                    ],
                    "required": False,
                    "name": "next_step_id",
                }
            ],
            "menu_options": ["addon_execute_start", "addon_disable_boot"],
            "description_placeholders": {
                "reference": "test",
                "addon": "test",
            },
        }
    )

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "addon_execute_start"},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)


# Test disabled for now until repair can be re-enabled. First we need a repair
# specifically for the OTBR add-on to make migration to ZHA easy rather then
# having this repair encourage uninstall of that add-on and make migration hard.
@test.skip("disabled until OTBR-specific repair exists")
async def supervisor_issue_deprecated_addon() -> None:
    """Test fix flow for supervisor issue for deprecated add-on."""


@test
async def supervisor_issue_deprecated_arch_addon(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test fix flow for supervisor issue for add-on using deprecated architecture or machine."""
    _enable_addons(_setup)
    issue_uuid = uuid4()
    sugg_uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.DEPRECATED_ARCH_ADDON,
                context=ContextType.ADDON,
                reference="test",
                uuid=issue_uuid,
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=sugg_uuid,
                    auto=False,
                ),
            ]
        },
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    expect(repair_issue).to_be_truthy()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "form",
            "flow_id": flow_id,
            "handler": "hassio",
            "step_id": "addon_execute_remove",
            "data_schema": [],
            "errors": None,
            "description_placeholders": {
                "reference": "test",
                "addon": "test",
                "help_url": "https://www.home-assistant.io/help/",
                "community_url": "https://community.home-assistant.io/",
            },
            "last_step": True,
            "preview": None,
        }
    )

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    expect(resp.status).to_equal(HTTPStatus.OK)
    data = await resp.json()

    flow_id = data["flow_id"]
    expect(data).to_equal(
        {
            "type": "create_entry",
            "flow_id": flow_id,
            "handler": "hassio",
            "description": None,
            "description_placeholders": None,
        }
    )

    expect(
        issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    ).to_be_falsy()
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)
