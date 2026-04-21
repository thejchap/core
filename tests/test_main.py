"""Test methods in __main__."""

from __future__ import annotations

import argparse
from unittest.mock import PropertyMock, patch

from tryke import expect, test

from homeassistant import __main__ as main
from homeassistant.const import REQUIRED_PYTHON_VER, RESTART_EXIT_CODE


@test
def validate_python() -> None:
    """Test validate Python version method."""
    with patch("sys.exit") as mock_exit:
        with patch(
            "sys.version_info", new_callable=PropertyMock(return_value=(2, 7, 8))
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_truthy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info", new_callable=PropertyMock(return_value=(3, 2, 0))
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_truthy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info", new_callable=PropertyMock(return_value=(3, 4, 2))
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_truthy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info", new_callable=PropertyMock(return_value=(3, 5, 2))
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_truthy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info",
            new_callable=PropertyMock(
                return_value=(REQUIRED_PYTHON_VER[0] - 1, *REQUIRED_PYTHON_VER[1:])
            ),
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_truthy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info",
            new_callable=PropertyMock(return_value=REQUIRED_PYTHON_VER),
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_falsy()

        mock_exit.reset_mock()

        with patch(
            "sys.version_info",
            new_callable=PropertyMock(
                return_value=(*REQUIRED_PYTHON_VER[:2], REQUIRED_PYTHON_VER[2] + 1)
            ),
        ):
            main.validate_python()
            expect(mock_exit.called).to_be_falsy()


@test
def skip_pip_mutually_exclusive() -> None:
    """Test --skip-pip and --skip-pip-package are mutually exclusive."""
    with patch("sys.exit") as mock_exit:

        def parse_args(*args: str) -> argparse.Namespace:
            with patch("sys.argv", ["python", *args]):
                return main.get_arguments()

        args = parse_args("--skip-pip")
        expect(args.skip_pip).to_be_truthy()

        args = parse_args("--skip-pip-packages", "foo")
        expect(args.skip_pip).to_be_falsy()
        expect(args.skip_pip_packages).to_equal(["foo"])

        args = parse_args("--skip-pip-packages", "foo-asd,bar-xyz")
        expect(args.skip_pip).to_be_falsy()
        expect(args.skip_pip_packages).to_equal(["foo-asd", "bar-xyz"])

        expect(mock_exit.called).to_be_falsy()
        parse_args("--skip-pip", "--skip-pip-packages", "foo")
        expect(mock_exit.called).to_be_truthy()


@test
def restart_after_backup_restore() -> None:
    """Test restarting if we restored a backup."""
    with (
        patch("sys.argv", ["python"]),
        patch("homeassistant.__main__.restore_backup", return_value=True),
    ):
        exit_code = main.main()
        expect(exit_code).to_equal(RESTART_EXIT_CODE)
