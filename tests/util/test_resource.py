"""Test the resource utility module."""

import os
import resource
from unittest.mock import call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.util.resource import (
    DEFAULT_SOFT_FILE_LIMIT,
    set_open_file_descriptor_limit,
)

from tests.hass_fixtures import LogCapture, caplog


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported fixtures resolve via Depends()."""
    return 0


@test.cases(
    test.case(
        "small-soft",
        original_soft=1024,
        expected_calls=[
            call(resource.RLIMIT_NOFILE, (DEFAULT_SOFT_FILE_LIMIT, 524288))
        ],
        should_log_already_sufficient=False,
    ),
    test.case(
        "just-below-default",
        original_soft=DEFAULT_SOFT_FILE_LIMIT - 1,
        expected_calls=[
            call(resource.RLIMIT_NOFILE, (DEFAULT_SOFT_FILE_LIMIT, 524288))
        ],
        should_log_already_sufficient=False,
    ),
    test.case(
        "at-default",
        original_soft=DEFAULT_SOFT_FILE_LIMIT,
        expected_calls=[],
        should_log_already_sufficient=True,
    ),
    test.case(
        "above-default",
        original_soft=DEFAULT_SOFT_FILE_LIMIT + 1,
        expected_calls=[],
        should_log_already_sufficient=True,
    ),
)
def set_open_file_descriptor_limit_default(
    original_soft: int,
    expected_calls: list,
    should_log_already_sufficient: bool,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test setting file limit with default value."""
    original_hard = 524288
    with (
        patch(
            "homeassistant.util.resource.resource.getrlimit",
            return_value=(original_soft, original_hard),
        ),
        patch("homeassistant.util.resource.resource.setrlimit") as mock_setrlimit,
    ):
        set_open_file_descriptor_limit()

    expect(mock_setrlimit.call_args_list).to_equal(expected_calls)
    expect(
        (f"Current soft limit ({original_soft}) is already" in caplog.text)
        is should_log_already_sufficient
    ).to_be(True)


@test.cases(
    test.case(
        "below-custom",
        original_soft=1499,
        custom_limit=1500,
        expected_calls=[call(resource.RLIMIT_NOFILE, (1500, 524288))],
        should_log_already_sufficient=False,
    ),
    test.case(
        "at-custom",
        original_soft=1500,
        custom_limit=1500,
        expected_calls=[],
        should_log_already_sufficient=True,
    ),
    test.case(
        "above-custom",
        original_soft=1501,
        custom_limit=1500,
        expected_calls=[],
        should_log_already_sufficient=True,
    ),
)
def set_open_file_descriptor_limit_environment_variable(
    original_soft: int,
    custom_limit: int,
    expected_calls: list,
    should_log_already_sufficient: bool,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test setting file limit from environment variable."""
    original_hard = 524288
    with (
        patch.dict(os.environ, {"SOFT_FILE_LIMIT": str(custom_limit)}),
        patch(
            "homeassistant.util.resource.resource.getrlimit",
            return_value=(original_soft, original_hard),
        ),
        patch("homeassistant.util.resource.resource.setrlimit") as mock_setrlimit,
    ):
        set_open_file_descriptor_limit()

    expect(mock_setrlimit.call_args_list).to_equal(expected_calls)
    expect(
        (f"Current soft limit ({original_soft}) is already" in caplog.text)
        is should_log_already_sufficient
    ).to_be(True)


@test
def set_open_file_descriptor_limit_exceeds_hard_limit(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test setting file limit that exceeds hard limit."""
    original_soft, original_hard = (1024, 524288)
    excessive_limit = original_hard + 1

    with (
        patch.dict(os.environ, {"SOFT_FILE_LIMIT": str(excessive_limit)}),
        patch(
            "homeassistant.util.resource.resource.getrlimit",
            return_value=(original_soft, original_hard),
        ),
        patch("homeassistant.util.resource.resource.setrlimit") as mock_setrlimit,
    ):
        set_open_file_descriptor_limit()

    mock_setrlimit.assert_called_once_with(
        resource.RLIMIT_NOFILE, (original_hard, original_hard)
    )
    expect(
        f"Requested soft limit ({excessive_limit}) exceeds hard limit ({original_hard})"
        in caplog.text
    ).to_be(True)


@test
def set_open_file_descriptor_limit_os_error(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test handling OSError when setting file limit."""
    with (
        patch(
            "homeassistant.util.resource.resource.getrlimit",
            return_value=(1024, 524288),
        ),
        patch(
            "homeassistant.util.resource.resource.setrlimit",
            side_effect=OSError("Permission denied"),
        ),
    ):
        set_open_file_descriptor_limit()

    expect("Failed to set file descriptor limit" in caplog.text).to_be(True)
    expect("Permission denied" in caplog.text).to_be(True)


@test
def set_open_file_descriptor_limit_value_error(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test handling ValueError when setting file limit."""
    with (
        patch.dict(os.environ, {"SOFT_FILE_LIMIT": "invalid_value"}),
        patch(
            "homeassistant.util.resource.resource.getrlimit",
            return_value=(1024, 524288),
        ),
    ):
        set_open_file_descriptor_limit()

    expect("Invalid file descriptor limit value" in caplog.text).to_be(True)
    expect("'invalid_value'" in caplog.text).to_be(True)
