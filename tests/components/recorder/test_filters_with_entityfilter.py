"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def included_and_excluded_simple_case_no_domains() -> None:
    """Stub for test_included_and_excluded_simple_case_no_domains (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def included_and_excluded_simple_case_no_globs() -> None:
    """Stub for test_included_and_excluded_simple_case_no_globs (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def included_and_excluded_simple_case_without_underscores() -> None:
    """Stub for test_included_and_excluded_simple_case_without_underscores (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def included_and_excluded_simple_case_with_underscores() -> None:
    """Stub for test_included_and_excluded_simple_case_with_underscores (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def included_and_excluded_complex_case() -> None:
    """Stub for test_included_and_excluded_complex_case (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def included_entities_and_excluded_domain() -> None:
    """Stub for test_included_entities_and_excluded_domain (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def same_domain_included_excluded() -> None:
    """Stub for test_same_domain_included_excluded (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def same_entity_included_excluded() -> None:
    """Stub for test_same_entity_included_excluded (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def same_entity_included_excluded_include_domain_wins() -> None:
    """Stub for test_same_entity_included_excluded_include_domain_wins (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def specificly_included_entity_always_wins() -> None:
    """Stub for test_specificly_included_entity_always_wins (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def specificly_included_entity_always_wins_over_glob() -> None:
    """Stub for test_specificly_included_entity_always_wins_over_glob (port deferred)."""
