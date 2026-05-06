"""Test methods in backup_restore."""

from __future__ import annotations

import json
from pathlib import Path
import tarfile
from typing import Any
from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant import backup_restore

from .common import get_fixture_path
from .hass_fixtures import tmp_path


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def _expect_raises(
    exc_type: type[BaseException], fn: Any, *args: Any, **kwargs: Any
) -> BaseException:
    try:
        fn(*args, **kwargs)
    except exc_type as err:
        return err
    raise AssertionError(f"Expected {exc_type.__name__}")


def restore_result_file_content(config_dir: Path) -> dict[str, Any] | None:
    """Return the content of the restore result file."""
    try:
        return json.loads((config_dir / ".HA_RESTORE_RESULT").read_text("utf-8"))
    except FileNotFoundError:
        return None


_RESTORE3_CONTENT = backup_restore.RestoreBackupFileContent(
    backup_file_path=Path("test"),
    password="psw",
    remove_after_restore=False,
    restore_database=False,
    restore_homeassistant=True,
)
_RESTORE4_CONTENT = backup_restore.RestoreBackupFileContent(
    backup_file_path=Path("test"),
    password=None,
    remove_after_restore=True,
    restore_database=True,
    restore_homeassistant=False,
)


@test.cases(
    test.case(
        "empty_file",
        restore_config="restore1.json",
        expected=None,
        restore_result={
            "success": False,
            "error": "Expecting value: line 1 column 1 (char 0)",
            "error_type": "JSONDecodeError",
        },
    ),
    test.case(
        "missing_password_key",
        restore_config="restore2.json",
        expected=None,
        restore_result={
            "success": False,
            "error": "'password'",
            "error_type": "KeyError",
        },
    ),
    test.case(
        "restore3",
        restore_config="restore3.json",
        expected=_RESTORE3_CONTENT,
        restore_result=None,
    ),
    test.case(
        "restore4",
        restore_config="restore4.json",
        expected=_RESTORE4_CONTENT,
        restore_result=None,
    ),
)
def reading_the_instruction_contents(
    restore_config: str,
    expected: backup_restore.RestoreBackupFileContent | None,
    restore_result: dict[str, Any] | None,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test reading the content of the .HA_RESTORE file."""
    get_fixture_path(f"core/backup_restore/{restore_config}", None).copy(
        tmp_path / ".HA_RESTORE"
    )
    restore_file_path = tmp_path / ".HA_RESTORE"
    expect(restore_file_path.exists()).to_be_truthy()

    read_content = backup_restore.restore_backup_file_content(tmp_path)
    expect(read_content).to_equal(expected)
    expect(restore_file_path.exists()).to_be_falsy()
    expect(restore_result_file_content(tmp_path)).to_equal(restore_result)


@test
def reading_the_instruction_contents_missing(
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test reading the content of the .HA_RESTORE file when it is missing."""
    expect((tmp_path / ".HA_RESTORE").exists()).to_be_falsy()

    read_content = backup_restore.restore_backup_file_content(tmp_path)
    expect(read_content).to_be_none()
    expect((tmp_path / ".HA_RESTORE").exists()).to_be_falsy()
    expect(restore_result_file_content(tmp_path)).to_be_none()


@test.cases(
    test.case("restore3", restore_config="restore3.json"),
    test.case("restore4", restore_config="restore4.json"),
)
def restoring_backup_that_does_not_exist(
    restore_config: str,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test restoring a backup that does not exist."""
    get_fixture_path(f"core/backup_restore/{restore_config}", None).copy(
        tmp_path / ".HA_RESTORE"
    )
    restore_file_path = tmp_path / ".HA_RESTORE"
    expect(restore_file_path.exists()).to_be_truthy()
    err = _expect_raises(ValueError, backup_restore.restore_backup, tmp_path.as_posix())
    expect(str(err)).to_contain("Backup file test does not exist")
    expect(restore_result_file_content(tmp_path)).to_equal(
        {
            "error": "Backup file test does not exist",
            "error_type": "ValueError",
            "success": False,
        }
    )


@test.cases(
    test.case(
        "empty_file",
        restore_config="restore1.json",
        restore_result={
            "success": False,
            "error": "Expecting value: line 1 column 1 (char 0)",
            "error_type": "JSONDecodeError",
        },
    ),
    test.case(
        "missing_password_key",
        restore_config="restore2.json",
        restore_result={
            "success": False,
            "error": "'password'",
            "error_type": "KeyError",
        },
    ),
)
def restoring_backup_when_instructions_can_not_be_read(
    restore_config: str,
    restore_result: dict[str, Any],
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test restoring a backup when instructions can not be read."""
    get_fixture_path(f"core/backup_restore/{restore_config}", None).copy(
        tmp_path / ".HA_RESTORE"
    )
    restore_file_path = tmp_path / ".HA_RESTORE"
    expect(restore_file_path.exists()).to_be_truthy()
    expect(backup_restore.restore_backup(tmp_path.as_posix())).to_be_falsy()
    expect(restore_file_path.exists()).to_be_falsy()
    expect(restore_result_file_content(tmp_path)).to_equal(restore_result)


@test
def restoring_backup_when_instructions_missing(
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test restoring a backup when instructions are missing."""
    restore_file_path = tmp_path / ".HA_RESTORE"
    expect(restore_file_path.exists()).to_be_falsy()
    expect(backup_restore.restore_backup(tmp_path.as_posix())).to_be_falsy()
    expect(restore_file_path.exists()).to_be_falsy()
    expect(restore_result_file_content(tmp_path)).to_be_none()


@test.cases(
    test.case("restore3", restore_config="restore3.json"),
    test.case("restore4", restore_config="restore4.json"),
)
def restoring_backup_that_is_not_a_file(
    restore_config: str,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test restoring a backup that is not a file."""
    backup_file_path = tmp_path / "test"
    restore_file_path = tmp_path / ".HA_RESTORE"

    # Set up restore file to point to a file within the temporary directory
    restore_config_data = json.loads(
        get_fixture_path(f"core/backup_restore/{restore_config}", None).read_text(
            encoding="utf-8"
        )
    )
    restore_config_data["path"] = backup_file_path.as_posix()
    restore_file_path.write_text(json.dumps(restore_config_data), encoding="utf-8")
    expect(restore_file_path.exists()).to_be_truthy()

    # Create a directory at the backup file path to simulate the backup file not being a file
    backup_file_path.mkdir(exist_ok=True)

    err = _expect_raises(
        IsADirectoryError, backup_restore.restore_backup, tmp_path.as_posix()
    )
    expect(str(err)).to_contain("[Errno 21] Is a directory")
    restore_result = restore_result_file_content(tmp_path)
    expect(restore_result).to_equal(
        {
            "error": mock.ANY,
            "error_type": "IsADirectoryError",
            "success": False,
        }
    )
    assert restore_result is not None  # for the type checker
    expect(
        restore_result["error"].startswith("[Errno 21] Is a directory:")
    ).to_be_truthy()


@test.cases(
    test.case("restore3", restore_config="restore3.json"),
    test.case("restore4", restore_config="restore4.json"),
)
def aborting_for_older_versions(
    restore_config: str,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test that we abort for older versions."""
    backup_file_path = tmp_path / "backup_from_future.tar"
    restore_file_path = tmp_path / ".HA_RESTORE"

    # Set up restore file to point to a file within the temporary directory
    restore_config_data = json.loads(
        get_fixture_path(f"core/backup_restore/{restore_config}", None).read_text(
            encoding="utf-8"
        )
    )
    restore_config_data["path"] = backup_file_path.as_posix()
    restore_file_path.write_text(json.dumps(restore_config_data), encoding="utf-8")
    expect(restore_file_path.exists()).to_be_truthy()

    get_fixture_path("core/backup_restore/backup_from_future.tar", None).copy_into(
        tmp_path
    )

    err = _expect_raises(ValueError, backup_restore.restore_backup, tmp_path.as_posix())
    expect(str(err)).to_contain(
        "You need at least Home Assistant version 9999.99.99 to restore this backup"
    )
    expect(restore_result_file_content(tmp_path)).to_equal(
        {
            "error": (
                "You need at least Home Assistant version 9999.99.99 to restore this backup"
            ),
            "error_type": "ValueError",
            "success": False,
        }
    )


_RESTORE_BACKUP_CASES: list[
    tuple[str, str, str | None, Any, set[str], set[str], set[str]]
] = [
    (backup_id, content_id, backup, password, content, kept, restored, dirs)
    for backup_id, backup, password in (
        ("plain", "backup_with_database.tar", None),
        ("protected_v2", "backup_with_database_protected_v2.tar", "hunter2"),
        ("protected_v3", "backup_with_database_protected_v3.tar", "hunter2"),
    )
    for content_id, content, kept, restored, dirs in (
        (
            "restore_db_ha",
            backup_restore.RestoreBackupFileContent(
                backup_file_path=None,
                password=None,
                remove_after_restore=False,
                restore_database=True,
                restore_homeassistant=True,
            ),
            {"backups/test.tar"},
            {"home-assistant_v2.db", "home-assistant_v2.db-wal"},
            {"backups"},
        ),
        (
            "restore_ha_only",
            backup_restore.RestoreBackupFileContent(
                backup_file_path=None,
                password=None,
                restore_database=False,
                remove_after_restore=False,
                restore_homeassistant=True,
            ),
            {"backups/test.tar", "home-assistant_v2.db", "home-assistant_v2.db-wal"},
            set(),
            {"backups"},
        ),
        (
            "restore_db_only",
            backup_restore.RestoreBackupFileContent(
                backup_file_path=None,
                password=None,
                restore_database=True,
                remove_after_restore=False,
                restore_homeassistant=False,
            ),
            {".HA_RESTORE", ".HA_VERSION", "backups/test.tar"},
            {"home-assistant_v2.db", "home-assistant_v2.db-wal"},
            {"backups", "tmp_backups", "www"},
        ),
    )
]


@test.cases(
    test.case(
        "plain__restore_db_ha",
        backup="backup_with_database.tar",
        password=None,
        restore_backup_content=_RESTORE_BACKUP_CASES[0][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[0][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[0][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[0][7],
    ),
    test.case(
        "plain__restore_ha_only",
        backup="backup_with_database.tar",
        password=None,
        restore_backup_content=_RESTORE_BACKUP_CASES[1][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[1][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[1][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[1][7],
    ),
    test.case(
        "plain__restore_db_only",
        backup="backup_with_database.tar",
        password=None,
        restore_backup_content=_RESTORE_BACKUP_CASES[2][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[2][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[2][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[2][7],
    ),
    test.case(
        "protected_v2__restore_db_ha",
        backup="backup_with_database_protected_v2.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[0][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[0][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[0][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[0][7],
    ),
    test.case(
        "protected_v2__restore_ha_only",
        backup="backup_with_database_protected_v2.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[1][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[1][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[1][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[1][7],
    ),
    test.case(
        "protected_v2__restore_db_only",
        backup="backup_with_database_protected_v2.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[2][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[2][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[2][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[2][7],
    ),
    test.case(
        "protected_v3__restore_db_ha",
        backup="backup_with_database_protected_v3.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[0][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[0][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[0][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[0][7],
    ),
    test.case(
        "protected_v3__restore_ha_only",
        backup="backup_with_database_protected_v3.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[1][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[1][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[1][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[1][7],
    ),
    test.case(
        "protected_v3__restore_db_only",
        backup="backup_with_database_protected_v3.tar",
        password="hunter2",
        restore_backup_content=_RESTORE_BACKUP_CASES[2][4],
        expected_kept_files=_RESTORE_BACKUP_CASES[2][5],
        expected_restored_files=_RESTORE_BACKUP_CASES[2][6],
        expected_directories_after_restore=_RESTORE_BACKUP_CASES[2][7],
    ),
)
def restore_backup(
    backup: str,
    password: str | None,
    restore_backup_content: backup_restore.RestoreBackupFileContent,
    expected_kept_files: set[str],
    expected_restored_files: set[str],
    expected_directories_after_restore: set[str],
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test restoring a backup.

    This includes checking that expected files are kept, restored, and
    that we are cleaning up the current configuration directory.
    """
    backup_file_path = tmp_path / "backups" / "test.tar"

    def get_files(path: Path) -> set[str]:
        """Get all files under path."""
        return {str(f.relative_to(path)) for f in path.rglob("*")}

    existing_dirs = {
        "backups",
        "tmp_backups",
        "www",
    }
    existing_files = {
        ".HA_RESTORE",
        ".HA_VERSION",
        "home-assistant_v2.db",
        "home-assistant_v2.db-wal",
    }

    for d in existing_dirs:
        (tmp_path / d).mkdir(exist_ok=True)
    for f in existing_files:
        (tmp_path / f).write_text("before_restore")

    get_fixture_path(f"core/backup_restore/{backup}", None).copy(backup_file_path)

    files_before_restore = get_files(tmp_path)
    expect(files_before_restore).to_equal(
        {
            ".HA_RESTORE",
            ".HA_VERSION",
            "backups",
            "backups/test.tar",
            "home-assistant_v2.db",
            "home-assistant_v2.db-wal",
            "tmp_backups",
            "www",
        }
    )
    kept_files_data = {}
    for file in expected_kept_files:
        kept_files_data[file] = (tmp_path / file).read_bytes()

    restore_backup_content.backup_file_path = backup_file_path
    restore_backup_content.password = password

    with (
        mock.patch(
            "homeassistant.backup_restore.restore_backup_file_content",
            return_value=restore_backup_content,
        ),
    ):
        expect(backup_restore.restore_backup(tmp_path.as_posix())).to_be_truthy()

    files_after_restore = get_files(tmp_path)
    expect(files_after_restore).to_equal(
        {".HA_RESTORE_RESULT"}
        | expected_kept_files
        | expected_restored_files
        | expected_directories_after_restore
    )

    for d in expected_directories_after_restore:
        expect((tmp_path / d).is_dir()).to_be_truthy()
    for file in expected_kept_files:
        expect((tmp_path / file).read_bytes()).to_equal(kept_files_data[file])
    for file in expected_restored_files:
        expect((tmp_path / file).read_bytes()).to_equal(b"restored_from_backup")

    expect(restore_result_file_content(tmp_path)).to_equal(
        {
            "error": None,
            "error_type": None,
            "success": True,
        }
    )


@test
def restore_backup_filter_files(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test filtering dangerous files when restoring a backup."""
    backup_file_path = tmp_path / "backups" / "test.tar"
    backup_file_path.parent.mkdir()
    get_fixture_path(
        "core/backup_restore/malicious_backup_with_database.tar", None
    ).copy(backup_file_path)

    with (
        tarfile.open(backup_file_path, "r") as outer_tar,
        tarfile.open(
            fileobj=outer_tar.extractfile("homeassistant.tar.gz"), mode="r|gz"
        ) as inner_tar,
    ):
        member_names = {member.name for member in inner_tar.getmembers()}
        expect(member_names).to_equal(
            {
                ".",
                "../bad_file_with_parent_link",
                "/bad_absolute_file",
                "data",
                "data/home-assistant_v2.db",
                "data/home-assistant_v2.db-wal",
            }
        )

    real_extractone = tarfile.TarFile._extract_one

    with (
        mock.patch(
            "homeassistant.backup_restore.restore_backup_file_content",
            return_value=backup_restore.RestoreBackupFileContent(
                backup_file_path=backup_file_path,
                password=None,
                remove_after_restore=False,
                restore_database=True,
                restore_homeassistant=True,
            ),
        ),
        mock.patch(
            "tarfile.TarFile._extract_one", autospec=True, wraps=real_extractone
        ) as extractone_mock,
    ):
        expect(backup_restore.restore_backup(tmp_path.as_posix())).to_be_truthy()

    # Check the unsafe files are not extracted, and that the safe files are extracted
    extracted_files = {call.args[1].name for call in extractone_mock.mock_calls}
    expect(extracted_files).to_equal(
        {
            "./backup.json",  # From the outer tar
            "homeassistant.tar.gz",  # From the outer tar
            ".",
            "data",
            "data/home-assistant_v2.db",
            "data/home-assistant_v2.db-wal",
        }
    )
    expect(restore_result_file_content(tmp_path)).to_equal(
        {
            "error": None,
            "error_type": None,
            "success": True,
        }
    )


@test.cases(
    test.case("remove_true", remove_after_restore=True),
    test.case("remove_false", remove_after_restore=False),
)
def remove_backup_file_after_restore(
    remove_after_restore: bool,
    tmp_path: Path = Depends(tmp_path),
) -> None:
    """Test removing a backup file after restore."""
    backup_file_path = tmp_path / "backups" / "test.tar"
    backup_file_path.parent.mkdir()
    get_fixture_path("core/backup_restore/backup_with_database.tar", None).copy(
        backup_file_path
    )

    with (
        mock.patch(
            "homeassistant.backup_restore.restore_backup_file_content",
            return_value=backup_restore.RestoreBackupFileContent(
                backup_file_path=backup_file_path,
                password=None,
                remove_after_restore=remove_after_restore,
                restore_database=True,
                restore_homeassistant=True,
            ),
        ),
    ):
        expect(backup_restore.restore_backup(tmp_path.as_posix())).to_be_truthy()
    expect(backup_file_path.exists()).to_equal(not remove_after_restore)
    expect(restore_result_file_content(tmp_path)).to_equal(
        {
            "error": None,
            "error_type": None,
            "success": True,
        }
    )
