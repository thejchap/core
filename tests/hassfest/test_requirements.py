"""Tests for hassfest requirements."""

import contextlib
from collections.abc import Generator
from importlib.metadata import PackagePath
from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from script.hassfest import requirements as req_module
from script.hassfest.model import Config, Integration
from script.hassfest.requirements import (
    PACKAGE_CHECK_PREPARE_UPDATE,
    PACKAGE_CHECK_VERSION_RANGE,
    _packages_checked_files_cache,
    check_dependency_files,
    check_dependency_version_range,
    validate_requirements_format,
)


@fixture
def integration() -> Integration:
    """Fixture for hassfest integration model."""
    return Integration(
        path=Path("homeassistant/components/test").absolute(),
        _config=Config(
            root=Path(".").absolute(),
            specific_integrations=None,
            action="validate",
            requirements=True,
        ),
        _manifest={
            "domain": "test",
            "documentation": "https://example.com",
            "name": "test",
            "codeowners": ["@awesome"],
            "requirements": [],
        },
    )


@contextlib.contextmanager
def _mock_forbidden_package_names() -> Generator[None]:
    """Patch FORBIDDEN_PACKAGE_NAMES on the requirements module."""
    original = req_module.FORBIDDEN_PACKAGE_NAMES
    req_module.FORBIDDEN_PACKAGE_NAMES = {"test", "tests"}
    try:
        yield
    finally:
        req_module.FORBIDDEN_PACKAGE_NAMES = original


@test
def validate_requirements_format_with_space(
    integration: Integration = Depends(integration),
) -> None:
    """Test validate requirement with space around separator."""
    integration.manifest["requirements"] = ["test_package == 1"]
    expect(bool(validate_requirements_format(integration))).to_be(False)
    expect(len(integration.errors)).to_equal(1)
    expect(
        'Requirement "test_package == 1" contains a space'
        in [x.error for x in integration.errors]
    ).to_be(True)


@test
def validate_requirements_format_wrongly_pinned(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement with loose pin."""
    integration.manifest["requirements"] = ["test_package>=1"]
    expect(bool(validate_requirements_format(integration))).to_be(False)
    expect(len(integration.errors)).to_equal(1)
    expect(
        'Requirement test_package>=1 need to be pinned "<pkg name>==<version>".'
        in [x.error for x in integration.errors]
    ).to_be(True)


@test
def validate_requirements_format_ignore_pin_for_custom(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement ignore pinning for custom."""
    integration.manifest["requirements"] = [
        "test_package>=1",
        "test_package",
        "test_package>=1.2.3,<3.2.1",
        "test_package~=0.5.0",
        "test_package>=1.4.2,<1.4.99,>=1.7,<1.8.99",
        "test_package>=1.4.2,<1.9,!=1.5",
        "test_package>=1.4.2;python_version<'3.11'",
    ]
    integration.path = Path("")
    expect(bool(validate_requirements_format(integration))).to_be(True)
    expect(len(integration.errors)).to_equal(0)


@test
def validate_requirements_format_invalid_version(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement with invalid version."""
    integration.manifest["requirements"] = ["test_package==invalid"]
    expect(bool(validate_requirements_format(integration))).to_be(False)
    expect(len(integration.errors)).to_equal(1)
    expect(
        "Unable to parse package version (invalid) for test_package."
        in [x.error for x in integration.errors]
    ).to_be(True)


@test
def validate_requirements_format_successful(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement with successful result."""
    integration.manifest["requirements"] = [
        "test_package==1.2.3",
        "test_package[async]==1.2.3",
        "test_package[async,encrypted]==1.2.3",
    ]
    expect(bool(validate_requirements_format(integration))).to_be(True)
    expect(len(integration.errors)).to_equal(0)


@test
def validate_requirements_format_github_core(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement that points to github fails with core component."""
    integration.manifest["requirements"] = [
        "git+https://github.com/user/project.git@1.2.3",
    ]
    expect(bool(validate_requirements_format(integration))).to_be(False)
    expect(len(integration.errors)).to_equal(1)


@test
def validate_requirements_format_github_custom(
    integration: Integration = Depends(integration),
) -> None:
    """Test requirement that points to github succeeds with custom component."""
    integration.manifest["requirements"] = [
        "git+https://github.com/user/project.git@1.2.3",
    ]
    integration.path = Path("")
    expect(bool(validate_requirements_format(integration))).to_be(True)
    expect(len(integration.errors)).to_equal(0)


@test.cases(
    test.case("gt2", version=">2", result=True),
    test.case("gte2_0", version=">=2.0", result=True),
    test.case("gte2_0_lt4", version=">=2.0,<4", result=True),
    test.case("lt4", version="<4", result=True),
    test.case("lte3_0", version="<=3.0", result=True),
    test.case(
        "gte2_0_lt4_pyver",
        version=">=2.0,<4;python_version<'3.14'",
        result=True,
    ),
    test.case("lt3", version="<3", result=False),
    test.case("eq2_star", version="==2.*", result=False),
    test.case("approx2_0", version="~=2.0", result=False),
    test.case("lte2_100", version="<=2.100", result=False),
    test.case("gt2_lt3", version=">2,<3", result=False),
    test.case("gte2_0_lt3", version=">=2.0,<3", result=False),
    test.case(
        "gte2_0_lt3_pyver",
        version=">=2.0,<3;python_version<'3.14'",
        result=False,
    ),
)
def dependency_version_range_prepare_update(
    version: str,
    result: bool,
    integration: Integration = Depends(integration),
) -> None:
    """Test dependency version range check for prepare update is working correctly."""
    with (
        patch.dict(PACKAGE_CHECK_VERSION_RANGE, {"numpy-test": "SemVer"}, clear=True),
        patch.dict(PACKAGE_CHECK_PREPARE_UPDATE, {"numpy-test": 3}, clear=True),
    ):
        expect(
            check_dependency_version_range(
                integration,
                "test",
                pkg="numpy-test",
                version=version,
                package_exceptions=set(),
            )
        ).to_equal(result)


@test
def check_dependency_package_names(
    integration: Integration = Depends(integration),
) -> None:
    """Test dependency package names check for forbidden package names."""
    with _mock_forbidden_package_names():
        package = "homeassistant"
        pkg = "my_package"

        pkg_files = [
            PackagePath("my_package/__init__.py"),
            PackagePath("my_package-1.0.0.dist-info/METADATA"),
            PackagePath("tests/test_some_function.py"),
            PackagePath("test/submodule/test_some_other_function.py"),
        ]
        with (
            patch(
                "script.hassfest.requirements.files", return_value=pkg_files
            ) as mock_files,
            patch.dict(_packages_checked_files_cache, {}, clear=True),
        ):
            expect(bool(_packages_checked_files_cache)).to_be(False)
            expect(check_dependency_files(integration, package, pkg, ())).to_be(False)
            expect(_packages_checked_files_cache[pkg]["top_level"]).to_equal(
                {"tests", "test"}
            )
            expect(len(integration.errors)).to_equal(2)
            expect(
                f"Package {pkg} has a forbidden top level directory 'tests' in {package}"
                in [x.error for x in integration.errors]
            ).to_be(True)
            expect(
                f"Package {pkg} has a forbidden top level directory 'test' in {package}"
                in [x.error for x in integration.errors]
            ).to_be(True)
            integration.errors.clear()

            expect(check_dependency_files(integration, package, pkg, ())).to_be(False)
            expect(mock_files.call_count).to_equal(1)
            expect(len(integration.errors)).to_equal(2)
            integration.errors.clear()

        pkg_files = [
            PackagePath("my_package/__init__.py"),
            PackagePath("my_package.dist-info/METADATA"),
            PackagePath("tests/test_some_function.py"),
        ]
        with (
            patch(
                "script.hassfest.requirements.files", return_value=pkg_files
            ) as mock_files,
            patch.dict(_packages_checked_files_cache, {}, clear=True),
        ):
            expect(bool(_packages_checked_files_cache)).to_be(False)
            expect(
                check_dependency_files(
                    integration, package, pkg, package_exceptions={pkg}
                )
            ).to_be(False)
            expect(_packages_checked_files_cache[pkg]["top_level"]).to_equal({"tests"})
            expect(len(integration.errors)).to_equal(0)
            expect(len(integration.warnings)).to_equal(1)
            expect(
                f"Package {pkg} has a forbidden top level directory 'tests' in {package}"
                in [x.error for x in integration.warnings]
            ).to_be(True)
            integration.warnings.clear()

            expect(
                check_dependency_files(
                    integration, package, pkg, package_exceptions={pkg}
                )
            ).to_be(False)
            expect(mock_files.call_count).to_equal(1)
            expect(len(integration.errors)).to_equal(0)
            expect(len(integration.warnings)).to_equal(1)
            integration.warnings.clear()

        pkg_files = [
            PackagePath("my_package/__init__.py"),
            PackagePath("my_package.dist-info/METADATA"),
        ]
        with (
            patch(
                "script.hassfest.requirements.files", return_value=pkg_files
            ) as mock_files,
            patch.dict(_packages_checked_files_cache, {}, clear=True),
        ):
            expect(bool(_packages_checked_files_cache)).to_be(False)
            expect(check_dependency_files(integration, package, pkg, ())).to_be(True)
            expect(_packages_checked_files_cache[pkg]["top_level"]).to_equal(set())
            expect(len(integration.errors)).to_equal(0)

            expect(check_dependency_files(integration, package, pkg, ())).to_be(True)
            expect(mock_files.call_count).to_equal(1)
            expect(len(integration.errors)).to_equal(0)


@test
def check_dependency_file_names(
    integration: Integration = Depends(integration),
) -> None:
    """Test dependency file name check for forbidden files."""
    package = "homeassistant"
    pkg = "my_package"

    pkg_files = [
        PackagePath("py.typed"),
        PackagePath("my_package.py"),
        PackagePath("some_script.Pth"),
        PackagePath("my_package-1.0.0.dist-info/METADATA"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        expect(bool(_packages_checked_files_cache)).to_be(False)
        expect(check_dependency_files(integration, package, pkg, ())).to_be(False)
        expect(_packages_checked_files_cache[pkg]["file_names"]).to_equal(
            {"py.typed", "some_script.Pth"}
        )
        expect(len(integration.errors)).to_equal(2)
        expect(
            f"Package {pkg} has a forbidden file 'py.typed' in {package}"
            in [x.error for x in integration.errors]
        ).to_be(True)
        expect(
            f"Package {pkg} has a forbidden file 'some_script.Pth' in {package}"
            in [x.error for x in integration.errors]
        ).to_be(True)
        integration.errors.clear()

        expect(check_dependency_files(integration, package, pkg, ())).to_be(False)
        expect(mock_files.call_count).to_equal(1)
        expect(len(integration.errors)).to_equal(2)
        integration.errors.clear()

    pkg_files = [
        PackagePath("my_package/__init__.py"),
        PackagePath("my_package/py.typed"),
        PackagePath("my_package.dist-info/METADATA"),
    ]
    with (
        patch(
            "script.hassfest.requirements.files", return_value=pkg_files
        ) as mock_files,
        patch.dict(_packages_checked_files_cache, {}, clear=True),
    ):
        expect(bool(_packages_checked_files_cache)).to_be(False)
        expect(check_dependency_files(integration, package, pkg, ())).to_be(True)
        expect(_packages_checked_files_cache[pkg]["file_names"]).to_equal(set())
        expect(len(integration.errors)).to_equal(0)

        expect(check_dependency_files(integration, package, pkg, ())).to_be(True)
        expect(mock_files.call_count).to_equal(1)
        expect(len(integration.errors)).to_equal(0)
