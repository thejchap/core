"""Tryke skip-stubs for test_init.py - recorder_mock fixture coupling."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.kitchen_sink module imports cleanly."""
    from homeassistant.components import kitchen_sink  # noqa: PLC0415
    expect(kitchen_sink).not_.to_be(None)


@test.skip("recorder_mock fixture coupling")
async def demo_statistics() -> None:
    """Stub for test_demo_statistics."""

@test.skip("recorder_mock fixture coupling")
async def demo_statistics_growth() -> None:
    """Stub for test_demo_statistics_growth."""

@test.skip("recorder_mock fixture coupling")
async def statistics_issues() -> None:
    """Stub for test_statistics_issues."""

@test.skip("recorder_mock fixture coupling")
async def issues_created() -> None:
    """Stub for test_issues_created."""

@test.skip("recorder_mock fixture coupling")
async def service() -> None:
    """Stub for test_service."""

@test.skip("recorder_mock fixture coupling")
async def special_repair_issue_not_created_when_disabled() -> None:
    """Stub for test_special_repair_issue_not_created_when_disabled."""

@test.skip("recorder_mock fixture coupling")
async def special_repair_issue_created_when_enabled() -> None:
    """Stub for test_special_repair_issue_created_when_enabled."""

@test.skip("recorder_mock fixture coupling")
async def special_repair_preview_feature_toggle() -> None:
    """Stub for test_special_repair_preview_feature_toggle."""

@test.skip("recorder_mock fixture coupling")
async def preview_feature_event_handler_registered() -> None:
    """Stub for test_preview_feature_event_handler_registered."""
