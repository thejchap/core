"""Test issues from supervisor issues."""

from collections.abc import Generator
from datetime import timedelta
import os
from typing import Any
from unittest.mock import ANY, AsyncMock, patch
from uuid import UUID, uuid4

from aiohasupervisor import (
    SupervisorBadRequestError,
    SupervisorError,
    SupervisorTimeoutError,
)
from aiohasupervisor.models import (
    Check,
    CheckType,
    ContextType,
    Issue,
    IssueType,
    ResolutionInfo,
    Suggestion,
    SuggestionType,
    UnhealthyReason,
    UnsupportedReason,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio.const import DATA_CONFIG_STORE
from homeassistant.components.repairs import DOMAIN as REPAIRS_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

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
    resolution_info,
    store_info,
    supervisor_client,
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
)

from tests.hass_fixtures import (
    caplog as caplog_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
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


@fixture
async def setup_repairs_fx(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the repairs integration."""
    assert await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})


@fixture
def resolution_suggestions_for_issue_fx(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock suggestions by issue from supervisor resolution."""
    supervisor_client.resolution.suggestions_for_issue.return_value = []
    return supervisor_client.resolution.suggestions_for_issue


@fixture
def all_setup_requests(
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _addon_stats: AsyncMock = Depends(addon_stats),
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
) -> tuple[AsyncMock, AsyncMock]:
    """Mock all setup requests (default: without addons)."""
    addons_list.return_value = []
    addon_installed.return_value.update_available = False
    addon_installed.return_value.version = "1.0.0"
    addon_installed.return_value.version_latest = "1.0.0"
    addon_installed.return_value.repository = "core"
    addon_installed.return_value.icon = False
    return addon_installed, addons_list


def _enable_addons(setup: tuple[AsyncMock, AsyncMock]) -> None:
    """Switch all_setup_requests to include_addons=True for this test."""
    from aiohasupervisor.models import (  # noqa: PLC0415
        AddonStage as _AddonStage,
        AddonState as _AddonState,
        InstalledAddon as _InstalledAddon,
    )

    addon_installed, addons_list = setup
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
            update_available=False,
            url="https://github.com/home-assistant/addons/test",
            version_latest="1.0.0",
            version="1.0.0",
            state=_AddonState.STARTED,
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
            version_latest="1.0.0",
            version="1.0.0",
            state=_AddonState.STARTED,
        ),
    ]
    addon_installed.return_value.update_available = False
    addon_installed.return_value.version = "1.0.0"
    addon_installed.return_value.version_latest = "1.0.0"
    addon_installed.return_value.repository = "core"
    addon_installed.return_value.icon = False


@fixture
def hass_supervisor_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
):
    """Return a websocket client authenticated as the Supervisor user."""

    async def create_client():
        hassio_user_id = hass.data[DATA_CONFIG_STORE].data.hassio_user
        hassio_user = await hass.auth.async_get_user(hassio_user_id)
        assert hassio_user
        assert hassio_user.refresh_tokens
        refresh_token = next(iter(hassio_user.refresh_tokens.values()))
        access_token = hass.auth.async_create_access_token(refresh_token)
        return await hass_ws_client(hass, access_token=access_token)

    return create_client


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


def _assert_repair_in_list(
    issues: list[dict[str, Any]], unhealthy: bool, reason: str
) -> None:
    """Assert repair for unhealthy/unsupported in list."""
    repair_type = "unhealthy" if unhealthy else "unsupported"
    assert {
        "breaks_in_ha_version": None,
        "created": ANY,
        "dismissed_version": None,
        "domain": "hassio",
        "ignored": False,
        "is_fixable": False,
        "issue_id": f"{repair_type}_system_{reason}",
        "issue_domain": None,
        "learn_more_url": f"https://www.home-assistant.io/more-info/{repair_type}/{reason}",
        "severity": "critical" if unhealthy else "warning",
        "translation_key": f"{repair_type}_{reason}",
        "translation_placeholders": None,
    } in issues


def _assert_issue_repair_in_list(
    issues: list[dict[str, Any]],
    uuid: str,
    context: str,
    type_: str,
    fixable: bool,
    *,
    reference: str | None = None,
    placeholders: dict[str, str] | None = None,
) -> None:
    """Assert repair for unhealthy/unsupported in list."""
    if reference:
        placeholders = (placeholders or {}) | {"reference": reference}
    assert {
        "breaks_in_ha_version": None,
        "created": ANY,
        "dismissed_version": None,
        "domain": "hassio",
        "ignored": False,
        "is_fixable": fixable,
        "issue_id": uuid,
        "issue_domain": None,
        "learn_more_url": None,
        "severity": "warning",
        "translation_key": f"issue_{context}_{type_}",
        "translation_placeholders": placeholders,
    } in issues


@test
async def unhealthy_issues(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test issues added for unhealthy systems."""
    _mock_resolution_info(
        supervisor_client, unhealthy=[UnhealthyReason.DOCKER, UnhealthyReason.SETUP]
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="docker")
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="setup")


@test.cases(
    test.case("docker", reason="docker"),
    test.case("docker_gateway_unprotected", reason="docker_gateway_unprotected"),
    test.case("duplicate_os_installation", reason="duplicate_os_installation"),
    test.case("oserror_bad_message", reason="oserror_bad_message"),
    test.case("privileged", reason="privileged"),
    test.case("setup", reason="setup"),
    test.case("supervisor", reason="supervisor"),
    test.case("untrusted", reason="untrusted"),
)
async def unhealthy_reasons(
    reason: str,
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test all unhealthy reasons in client library are properly made into repairs with a translation."""
    unhealthy_reason = UnhealthyReason(reason)
    _mock_resolution_info(supervisor_client, unhealthy=[unhealthy_reason])

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_repair_in_list(
        msg["result"]["issues"], unhealthy=True, reason=unhealthy_reason.value
    )


@test
async def unsupported_issues(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test issues added for unsupported systems."""
    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.CONNECTIVITY_CHECK, UnsupportedReason.OS],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    _assert_repair_in_list(
        msg["result"]["issues"], unhealthy=False, reason="connectivity_check"
    )
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=False, reason="os")


@test.cases(
    test.case("apparmor", reason="apparmor"),
    test.case("cgroup_version", reason="cgroup_version"),
    test.case("connectivity_check", reason="connectivity_check"),
    test.case("dbus", reason="dbus"),
    test.case("dns_server", reason="dns_server"),
    test.case("docker_configuration", reason="docker_configuration"),
    test.case("docker_version", reason="docker_version"),
    test.case("home_assistant_core_version", reason="home_assistant_core_version"),
    test.case("job_conditions", reason="job_conditions"),
    test.case("lxc", reason="lxc"),
    test.case("network_manager", reason="network_manager"),
    test.case("os", reason="os"),
    test.case("os_agent", reason="os_agent"),
    test.case("os_version", reason="os_version"),
    test.case("restart_policy", reason="restart_policy"),
    test.case("software", reason="software"),
    test.case("supervisor_version", reason="supervisor_version"),
    test.case("systemd", reason="systemd"),
    test.case("systemd_journal", reason="systemd_journal"),
    test.case("systemd_resolved", reason="systemd_resolved"),
    test.case("virtualization_image", reason="virtualization_image"),
)
async def unsupported_reasons(
    reason: str,
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test all unsupported reasons in client library are properly made into repairs with a translation."""
    unsupported_reason = UnsupportedReason(reason)
    _mock_resolution_info(supervisor_client, unsupported=[unsupported_reason])

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_repair_in_list(
        msg["result"]["issues"], unhealthy=False, reason=unsupported_reason.value
    )


@test
async def unhealthy_issues_add_remove(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test unhealthy issues added and removed from dispatches."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "health_changed",
                "data": {
                    "healthy": False,
                    "unhealthy_reasons": ["docker"],
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="docker")

    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "health_changed",
                "data": {"healthy": True},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"issues": []})


@test
async def unsupported_issues_add_remove(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test unsupported issues added and removed from dispatches."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "supported_changed",
                "data": {
                    "supported": False,
                    "unsupported_reasons": ["os"],
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=False, reason="os")

    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "supported_changed",
                "data": {"supported": True},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"issues": []})


@test
async def reset_issues_supervisor_restart(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """All issues reset on supervisor restart."""
    uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.OS],
        unhealthy=[UnhealthyReason.DOCKER],
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=uuid,
            )
        ],
        suggestions_by_issue={
            uuid: [
                Suggestion(
                    SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=uuid4(),
                    auto=False,
                )
            ]
        },
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(3)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="docker")
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=False, reason="os")
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=uuid.hex,
        context="system",
        type_="reboot_required",
        fixable=True,
        reference=None,
    )

    _mock_resolution_info(supervisor_client)
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"issues": []})


@test
async def no_reset_issues_supervisor_update_found(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Issues do not reset because a supervisor update was found."""
    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.OS],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)

    _mock_resolution_info(supervisor_client)
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)


@test
async def reasons_added_and_removed(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test an unsupported/unhealthy reasons being added and removed at same time."""
    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.OS],
        unhealthy=[UnhealthyReason.DOCKER],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="docker")
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=False, reason="os")

    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.CONNECTIVITY_CHECK],
        unhealthy=[UnhealthyReason.SETUP],
    )
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 3, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="setup")
    _assert_repair_in_list(
        msg["result"]["issues"], unhealthy=False, reason="connectivity_check"
    )


@test
async def ignored_unsupported_skipped(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Unsupported reasons which have an identical unhealthy reason are ignored."""
    _mock_resolution_info(
        supervisor_client,
        unsupported=[UnsupportedReason.PRIVILEGED],
        unhealthy=[UnhealthyReason.PRIVILEGED],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="privileged")


@test
async def new_unsupported_unhealthy_reason(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """New unsupported/unhealthy reasons result in a generic repair until next core update."""
    _mock_resolution_info(
        supervisor_client,
        unsupported=["fake_unsupported"],
        unhealthy=["fake_unhealthy"],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    assert {
        "breaks_in_ha_version": None,
        "created": ANY,
        "dismissed_version": None,
        "domain": "hassio",
        "ignored": False,
        "is_fixable": False,
        "issue_id": "unhealthy_system_fake_unhealthy",
        "issue_domain": None,
        "learn_more_url": "https://www.home-assistant.io/more-info/unhealthy/fake_unhealthy",
        "severity": "critical",
        "translation_key": "unhealthy",
        "translation_placeholders": {"reason": "fake_unhealthy"},
    } in msg["result"]["issues"]
    assert {
        "breaks_in_ha_version": None,
        "created": ANY,
        "dismissed_version": None,
        "domain": "hassio",
        "ignored": False,
        "is_fixable": False,
        "issue_id": "unsupported_system_fake_unsupported",
        "issue_domain": None,
        "learn_more_url": "https://www.home-assistant.io/more-info/unsupported/fake_unsupported",
        "severity": "warning",
        "translation_key": "unsupported",
        "translation_placeholders": {"reason": "fake_unsupported"},
    } in msg["result"]["issues"]


@test
async def supervisor_issues(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test repairs added for supervisor issue."""
    uuid_issue1 = uuid4()
    uuid_issue2 = uuid4()
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.DETACHED_ADDON_MISSING,
                context=ContextType.ADDON,
                reference="test",
                uuid=uuid_issue1,
            ),
            Issue(
                type=IssueType.MULTIPLE_DATA_DISKS,
                context=ContextType.SYSTEM,
                reference="/dev/sda1",
                uuid=uuid_issue2,
            ),
            Issue(
                type="should_not_be_repair",
                context=ContextType.OS,
                reference=None,
                uuid=uuid4(),
            ),
        ],
        suggestions_by_issue={
            uuid_issue2: [
                Suggestion(
                    type=SuggestionType.RENAME_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
                    uuid=uuid4(),
                    auto=False,
                )
            ]
        },
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(2)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=uuid_issue1.hex,
        context="addon",
        type_="detached_addon_missing",
        fixable=False,
        reference="test",
        placeholders={"addon_url": "/hassio/addon/test", "addon": "test"},
    )
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=uuid_issue2.hex,
        context="system",
        type_="multiple_data_disks",
        fixable=True,
        reference="/dev/sda1",
    )


@test
async def supervisor_issues_initial_failure(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    resolution_info: AsyncMock = Depends(resolution_info),
    hass_ws_client=Depends(hass_ws_client_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test issues manager retries after initial update failure."""
    uuid = uuid4()
    _mock_resolution_info(
        supervisor_client,
        unsupported=[],
        unhealthy=[],
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=uuid,
            )
        ],
        suggestions_by_issue={
            uuid: [
                Suggestion(
                    SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference=None,
                    uuid=uuid4(),
                    auto=False,
                )
            ]
        },
    )
    resolution_info.side_effect = [
        SupervisorBadRequestError("System is not ready with state: setup"),
        resolution_info.return_value,
    ]

    with patch("homeassistant.components.hassio.issues.REQUEST_REFRESH_DELAY", new=0.1):
        result = await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()
        expect(result).to_be_truthy()

        client = await hass_ws_client(hass)

        await client.send_json({"id": 1, "type": "repairs/list_issues"})
        msg = await client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(len(msg["result"]["issues"])).to_equal(0)

        freezer.tick(timedelta(milliseconds=200))
        await hass.async_block_till_done()
        await client.send_json({"id": 2, "type": "repairs/list_issues"})
        msg = await client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(len(msg["result"]["issues"])).to_equal(1)


@test
async def supervisor_issues_add_remove(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issues added and removed from dispatches."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "reboot_required",
                    "context": "system",
                    "reference": None,
                    "suggestions": [
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_reboot",
                            "context": "system",
                            "reference": None,
                        }
                    ],
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="reboot_required",
        fixable=True,
        reference=None,
    )

    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "issue_removed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "reboot_required",
                    "context": "system",
                    "reference": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"issues": []})


@test
async def supervisor_issues_suggestions_fail(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    resolution_suggestions_for_issue: AsyncMock = Depends(
        resolution_suggestions_for_issue_fx
    ),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test failing to get suggestions for issue skips it."""
    _mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference=None,
                uuid=uuid4(),
            )
        ],
    )
    resolution_suggestions_for_issue.side_effect = SupervisorTimeoutError

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(0)


@test
async def supervisor_remove_missing_issue_without_error(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test HA skips message to remove issue that it didn't know about (sync issue)."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    await client.send_json(
        {
            "id": 5,
            "type": "supervisor/event",
            "data": {
                "event": "issue_removed",
                "data": {
                    "uuid": "1234",
                    "type": "reboot_required",
                    "context": "system",
                    "reference": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()


@test
async def system_is_not_ready(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    resolution_info: AsyncMock = Depends(resolution_info),
    caplog=Depends(caplog_fx),
) -> None:
    """Ensure hassio starts despite error."""
    resolution_info.side_effect = SupervisorBadRequestError(
        "System is not ready with state: setup"
    )

    expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
    expect("Failed to update supervisor issues" in caplog.text).to_be_truthy()


@test
async def supervisor_issues_detached_addon_missing(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issue for detached addon due to missing repository."""
    _enable_addons(_setup)
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "detached_addon_missing",
                    "context": "addon",
                    "reference": "test",
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="addon",
        type_="detached_addon_missing",
        fixable=False,
        placeholders={
            "reference": "test",
            "addon": "test",
            "addon_url": "/hassio/addon/test",
        },
    )


@test
async def supervisor_issues_ntp_sync_failed(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issue for NTP sync failed."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "ntp_sync_failed",
                    "context": "system",
                    "reference": None,
                    "suggestions": [
                        {
                            "uuid": uuid4().hex,
                            "type": "enable_ntp",
                            "context": "system",
                            "reference": None,
                        }
                    ],
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="ntp_sync_failed",
        fixable=True,
        placeholders=None,
    )


@test
async def supervisor_issues_disk_lifetime(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issue for disk lifetime nearly exceeded."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "disk_lifetime",
                    "context": "system",
                    "reference": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="disk_lifetime",
        fixable=False,
        placeholders=None,
    )


@test
async def supervisor_issues_free_space(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issue for too little free space remaining."""
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "free_space",
                    "context": "system",
                    "reference": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="free_space",
        fixable=False,
        placeholders={
            "more_info_free_space": "https://www.home-assistant.io/more-info/free-space",
            "storage_url": "/config/storage",
            "free_space": "1.6",
        },
    )


@test
async def supervisor_issues_free_space_host_info_fail(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    host_info: AsyncMock = Depends(host_info),
) -> None:
    """Test supervisor issue for too little free space remaining without host info."""
    _mock_resolution_info(supervisor_client)
    host_info.side_effect = SupervisorError()

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "free_space",
                    "context": "system",
                    "reference": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="free_space",
        fixable=False,
        placeholders={
            "more_info_free_space": "https://www.home-assistant.io/more-info/free-space",
            "storage_url": "/config/storage",
            "free_space": "<2",
        },
    )


@test
async def supervisor_issues_addon_pwned(
    _env: None = Depends(fixture_supervisor_environ),
    _repairs: None = Depends(setup_repairs_fx),
    _setup: tuple = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test supervisor issue for pwned secret in an addon."""
    _enable_addons(_setup)
    _mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()

    client = await hass_supervisor_ws_client()

    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "pwned",
                    "context": "addon",
                    "reference": "test",
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"])).to_equal(1)
    _assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="addon",
        type_="pwned",
        fixable=False,
        placeholders={
            "reference": "test",
            "addon": "test",
            "addon_url": "/hassio/addon/test",
            "more_info_pwned": "https://www.home-assistant.io/more-info/pwned-passwords",
        },
    )
