"""Tryke skip stub for test_ai_task.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_generative_ai_conversation.ai_task module imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation import ai_task  # noqa: PLC0415
    expect(ai_task).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def generate_data() -> None:
    """Stub for test_generate_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def generate_image() -> None:
    """Stub for test_generate_image."""

