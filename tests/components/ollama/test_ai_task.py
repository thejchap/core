"""Tryke skip-stubs for ollama test_ai_task (port deferred)."""
from tryke import test

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def generate_data_with_unsupported_file_format() -> None:
    """Stub for test_generate_data_with_unsupported_file_format (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def generate_data() -> None:
    """Stub for test_generate_data (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def run_task_with_streaming() -> None:
    """Stub for test_run_task_with_streaming (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def run_task_connection_error() -> None:
    """Stub for test_run_task_connection_error (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def run_task_empty_response() -> None:
    """Stub for test_run_task_empty_response (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def generate_structured_data() -> None:
    """Stub for test_generate_structured_data (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def generate_invalid_structured_data() -> None:
    """Stub for test_generate_invalid_structured_data (port deferred)."""

@test.skip("requires ollama AsyncClient mocks + conversation infra (not ported)")
async def generate_data_with_attachment() -> None:
    """Stub for test_generate_data_with_attachment (port deferred)."""


