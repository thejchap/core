"""Tryke skip stub for test_services.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the habitica integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.habitica.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("habitica")


@test.skip("requires habiticalib mock chain + parametrize")
async def cast_skill() -> None:
    """Stub for test_cast_skill."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cast_skill_exceptions() -> None:
    """Stub for test_cast_skill_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_config_entry() -> None:
    """Stub for test_get_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def handle_quests() -> None:
    """Stub for test_handle_quests."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def handle_quests_exceptions() -> None:
    """Stub for test_handle_quests_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def score_task() -> None:
    """Stub for test_score_task."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def score_task_exceptions() -> None:
    """Stub for test_score_task_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def transformation() -> None:
    """Stub for test_transformation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def transformation_exceptions() -> None:
    """Stub for test_transformation_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_tasks() -> None:
    """Stub for test_get_tasks."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_task_exceptions() -> None:
    """Stub for test_update_task_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_task_exceptions() -> None:
    """Stub for test_create_task_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def task_not_found() -> None:
    """Stub for test_task_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_reward() -> None:
    """Stub for test_update_reward."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_reward() -> None:
    """Stub for test_create_reward."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_habit() -> None:
    """Stub for test_update_habit."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_habit() -> None:
    """Stub for test_create_habit."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_todo() -> None:
    """Stub for test_update_todo."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_todo() -> None:
    """Stub for test_create_todo."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_daily() -> None:
    """Stub for test_update_daily."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_daily() -> None:
    """Stub for test_create_daily."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_daily_service_validation_errors() -> None:
    """Stub for test_update_daily_service_validation_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tags() -> None:
    """Stub for test_tags."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_new_tag() -> None:
    """Stub for test_create_new_tag."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def create_new_tag_exception() -> None:
    """Stub for test_create_new_tag_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_tags() -> None:
    """Stub for test_remove_tags."""

