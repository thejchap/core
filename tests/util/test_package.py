"""Test Home Assistant package util methods."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from importlib.metadata import metadata
import logging
import os
from subprocess import PIPE
from unittest.mock import MagicMock, Mock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.util import package

from tests.hass_fixtures import LogCapture, caplog

RESOURCE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "resources")
)

TEST_NEW_REQ = "pyhelloworld3==1.0.0"

TEST_ZIP_REQ = f"file://{RESOURCE_DIR}/pyhelloworld3.zip#{TEST_NEW_REQ}"


@fixture
def mock_sys() -> Generator[MagicMock]:
    """Mock sys."""
    with patch("homeassistant.util.package.sys", spec=object) as sys_mock:
        sys_mock.executable = "python3"
        yield sys_mock


@fixture
def deps_dir() -> str:
    """Return path to deps directory."""
    return os.path.abspath("/deps_dir")


@fixture
def lib_dir(deps_dir: str = Depends(deps_dir)) -> str:
    """Return path to lib directory."""
    return os.path.join(deps_dir, "lib_dir")


@fixture
def mock_popen(lib_dir: str = Depends(lib_dir)) -> Generator[MagicMock]:
    """Return a Popen mock."""
    with patch("homeassistant.util.package.Popen") as popen_mock:
        popen_mock.return_value.__enter__ = popen_mock
        popen_mock.return_value.communicate.return_value = (
            bytes(lib_dir, "utf-8"),
            b"error",
        )
        popen_mock.return_value.returncode = 0
        yield popen_mock


@fixture
def mock_env_copy() -> Generator[Mock]:
    """Mock os.environ.copy."""
    with patch("homeassistant.util.package.os.environ.copy") as env_copy:
        env_copy.return_value = {}
        yield env_copy


@fixture
def mock_venv() -> Generator[MagicMock]:
    """Mock homeassistant.util.package.is_virtual_env."""
    with patch("homeassistant.util.package.is_virtual_env") as mock:
        mock.return_value = True
        yield mock


def mock_async_subprocess() -> MagicMock:
    """Return an async Popen mock."""
    async_popen = MagicMock()

    async def communicate(input=None):
        """Communicate mock."""
        stdout = bytes("/deps_dir/lib_dir", "utf-8")
        return (stdout, None)

    async_popen.communicate = communicate
    return async_popen


@test
def install(
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_sys: MagicMock = Depends(mock_sys),
    _venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test an install attempt on a package that doesn't exist."""
    env = mock_env_copy()
    expect(package.install_package(TEST_NEW_REQ, False)).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(
            [
                mock_sys.executable,
                "-m",
                "uv",
                "pip",
                "install",
                "--quiet",
                TEST_NEW_REQ,
                "--index-strategy",
                "unsafe-first-match",
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            close_fds=False,
        )
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test
def install_with_timeout(
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_sys: MagicMock = Depends(mock_sys),
    _venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test an install attempt on a package that doesn't exist with a timeout set."""
    env = mock_env_copy()
    expect(package.install_package(TEST_NEW_REQ, False, timeout=10)).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    env["HTTP_TIMEOUT"] = "10"
    expect(mock_popen.mock_calls[0]).to_equal(
        call(
            [
                mock_sys.executable,
                "-m",
                "uv",
                "pip",
                "install",
                "--quiet",
                TEST_NEW_REQ,
                "--index-strategy",
                "unsafe-first-match",
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            close_fds=False,
        )
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test
def install_upgrade(
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_sys: MagicMock = Depends(mock_sys),
    _venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test an upgrade attempt on a package."""
    env = mock_env_copy()
    expect(package.install_package(TEST_NEW_REQ)).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(
            [
                mock_sys.executable,
                "-m",
                "uv",
                "pip",
                "install",
                "--quiet",
                TEST_NEW_REQ,
                "--index-strategy",
                "unsafe-first-match",
                "--upgrade",
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            close_fds=False,
        )
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test.cases(
    test.case("in_venv", is_venv=True),
    test.case("not_in_venv", is_venv=False),
)
def install_target(
    is_venv: bool,
    mock_sys: MagicMock = Depends(mock_sys),
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test an install with a target."""
    target = "target_folder"
    env = mock_env_copy()
    abs_target = os.path.abspath(target)
    env["PYTHONUSERBASE"] = abs_target
    mock_venv.return_value = is_venv
    mock_sys.platform = "linux"
    args = [
        mock_sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--quiet",
        TEST_NEW_REQ,
        "--index-strategy",
        "unsafe-first-match",
        "--target",
        abs_target,
    ]

    expect(package.install_package(TEST_NEW_REQ, False, target=target)).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env, close_fds=False)
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test.cases(
    test.case("in_venv", in_venv=True, additional_env_vars={}),
    test.case(
        "UV_SYSTEM_PYTHON",
        in_venv=False,
        additional_env_vars={"UV_SYSTEM_PYTHON": "true"},
    ),
    test.case("UV_PYTHON", in_venv=False, additional_env_vars={"UV_PYTHON": "python3"}),
    test.case(
        "UV_SYSTEM_PYTHON and UV_PYTHON",
        in_venv=False,
        additional_env_vars={"UV_SYSTEM_PYTHON": "true", "UV_PYTHON": "python3"},
    ),
)
def install_pip_compatibility_no_workaround(
    in_venv: bool,
    additional_env_vars: dict[str, str],
    mock_sys: MagicMock = Depends(mock_sys),
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test install will not use pip fallback."""
    env = mock_env_copy()
    env.update(additional_env_vars)
    mock_venv.return_value = in_venv
    mock_sys.platform = "linux"
    args = [
        mock_sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--quiet",
        TEST_NEW_REQ,
        "--index-strategy",
        "unsafe-first-match",
    ]

    expect(package.install_package(TEST_NEW_REQ, False)).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env, close_fds=False)
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test
def install_pip_compatibility_use_workaround(
    mock_sys: MagicMock = Depends(mock_sys),
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test install will use pip compatibility fallback."""
    env = mock_env_copy()
    mock_venv.return_value = False
    mock_sys.platform = "linux"
    python = "python3"
    mock_sys.executable = python
    site_dir = "/site_dir"
    args = [
        mock_sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--quiet",
        TEST_NEW_REQ,
        "--index-strategy",
        "unsafe-first-match",
        "--python",
        python,
        "--target",
        site_dir,
    ]

    with patch("homeassistant.util.package.site", autospec=True) as site_mock:
        site_mock.getusersitepackages.return_value = site_dir
        expect(package.install_package(TEST_NEW_REQ, False)).to_be_truthy()

    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env, close_fds=False)
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test
def install_error(
    mock_popen: MagicMock = Depends(mock_popen),
    _sys: MagicMock = Depends(mock_sys),
    _venv: MagicMock = Depends(mock_venv),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test an install that errors out."""
    caplog.set_level(logging.WARNING)
    mock_popen.return_value.returncode = 1
    expect(package.install_package(TEST_NEW_REQ)).to_be_falsy()
    expect(len(caplog.records)).to_equal(1)
    for record in caplog.records:
        expect(record.levelname).to_equal("ERROR")


@test
def install_constraint(
    mock_popen: MagicMock = Depends(mock_popen),
    mock_env_copy: MagicMock = Depends(mock_env_copy),
    mock_sys: MagicMock = Depends(mock_sys),
    _venv: MagicMock = Depends(mock_venv),
) -> None:
    """Test install with constraint file on not installed package."""
    env = mock_env_copy()
    constraints = "constraints_file.txt"
    expect(
        package.install_package(TEST_NEW_REQ, False, constraints=constraints)
    ).to_be_truthy()
    expect(mock_popen.call_count).to_equal(2)
    expect(mock_popen.mock_calls[0]).to_equal(
        call(
            [
                mock_sys.executable,
                "-m",
                "uv",
                "pip",
                "install",
                "--quiet",
                TEST_NEW_REQ,
                "--index-strategy",
                "unsafe-first-match",
                "--constraint",
                constraints,
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            close_fds=False,
        )
    )
    expect(mock_popen.return_value.communicate.call_count).to_equal(1)


@test
async def async_get_user_site(
    mock_env_copy: MagicMock = Depends(mock_env_copy),
) -> None:
    """Test async get user site directory."""
    deps_dir = "/deps_dir"
    env = mock_env_copy()
    env["PYTHONUSERBASE"] = os.path.abspath(deps_dir)
    # mock_sys is a module-scoped fixture in Tryke (auto-runs for every
    # test), so package.sys.executable is the mocked value regardless of
    # whether this test depends on mock_sys.
    args = [package.sys.executable, "-m", "site", "--user-site"]
    with patch(
        "homeassistant.util.package.asyncio.create_subprocess_exec",
        return_value=mock_async_subprocess(),
    ) as popen_mock:
        ret = await package.async_get_user_site(deps_dir)
    expect(popen_mock.call_count).to_equal(1)
    expect(popen_mock.call_args).to_equal(
        call(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=env,
            close_fds=False,
        )
    )
    expect(ret).to_equal(os.path.join(deps_dir, "lib_dir"))


@test
async def async_get_installed_packages() -> None:
    """Test async get installed packages."""
    mock_output = b'[{"name": "package1", "version": "1.0.0"}, {"name": "package2", "version": "2.0.0"}]'

    async_popen = MagicMock()
    async_popen.returncode = 0

    async def communicate(input=None):
        return (mock_output, None)

    async_popen.communicate = communicate

    args = [package.sys.executable, "-m", "uv", "pip", "list", "--format", "json"]
    with patch(
        "homeassistant.util.package.asyncio.create_subprocess_exec",
        return_value=async_popen,
    ) as popen_mock:
        ret = await package.async_get_installed_packages()

    expect(popen_mock.call_count).to_equal(1)
    expect(popen_mock.call_args).to_equal(
        call(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            close_fds=False,
        )
    )
    expect(ret).to_equal(
        [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"},
        ]
    )


@test.cases(
    test.case("nonzero_return", returncode=1, stdout=b""),
    test.case(
        "json_object", returncode=0, stdout=b'{"name": "package1", "version": "1.0.0"}'
    ),
    test.case("json_string", returncode=0, stdout=b'"just a string"'),
)
async def async_get_installed_packages_returns_empty(
    returncode: int, stdout: bytes
) -> None:
    """Test async get installed packages returns empty list on errors."""
    async_popen = MagicMock()
    async_popen.returncode = returncode

    async def communicate(input=None):
        return (stdout, None)

    async_popen.communicate = communicate

    with patch(
        "homeassistant.util.package.asyncio.create_subprocess_exec",
        return_value=async_popen,
    ):
        ret = await package.async_get_installed_packages()

    expect(ret).to_equal([])


@test
def check_package_global(caplog: LogCapture = Depends(caplog)) -> None:
    """Test for an installed package."""
    pkg = metadata("homeassistant")
    installed_package = pkg["name"]
    installed_version = pkg["version"]

    expect(package.is_installed(installed_package)).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}=={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}>={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}<={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}<{installed_version}")
    ).to_be_falsy()

    expect(package.is_installed("-1 invalid_package")).to_be(False)
    expect("Invalid requirement '-1 invalid_package'" in caplog.text).to_be(True)


@test
def check_package_fragment(caplog: LogCapture = Depends(caplog)) -> None:
    """Test for an installed package with a fragment."""
    expect(package.is_installed(TEST_ZIP_REQ)).to_be_falsy()
    expect(
        package.is_installed("git+https://github.com/pypa/pip#pip>=1")
    ).to_be_truthy()
    expect(
        package.is_installed("git+https://github.com/pypa/pip#-1 invalid")
    ).to_be_falsy()
    expect(
        "Invalid requirement 'git+https://github.com/pypa/pip#-1 invalid'"
        in caplog.text
    ).to_be(True)


@test
def get_is_installed() -> None:
    """Test is_installed can parse complex requirements."""
    pkg = metadata("homeassistant")
    installed_package = pkg["name"]
    installed_version = pkg["version"]

    expect(package.is_installed(installed_package)).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}=={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}>={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}<={installed_version}")
    ).to_be_truthy()
    expect(
        package.is_installed(f"{installed_package}<{installed_version}")
    ).to_be_falsy()

    # URL-based requirements should always return False, as no version check is possible.
    expect(
        package.is_installed(
            "homeassistant@git+https://github.com/home-assistant/core.git@dev"
        )
    ).to_be_falsy()


@test
def check_package_previous_failed_install() -> None:
    """Test for when a previously install package failed and left cruft behind."""
    pkg = metadata("homeassistant")
    installed_package = pkg["name"]
    installed_version = pkg["version"]

    with patch("homeassistant.util.package.version", return_value=None):
        expect(package.is_installed(installed_package)).to_be_falsy()
        expect(
            package.is_installed(f"{installed_package}=={installed_version}")
        ).to_be_falsy()


async def _run_is_docker_env(
    dockerenv: bool,
    containerenv: bool,
    kubernetes_service_host: bool,
    is_official_image: bool,
) -> None:
    """Shared body for is_docker_env cases."""

    def new_path_mock(path: str):
        mock = Mock()
        if path == "/.dockerenv":
            mock.exists.return_value = dockerenv
        elif path == "/run/.containerenv":
            mock.exists.return_value = containerenv
        return mock

    env = {}
    if kubernetes_service_host:
        env["KUBERNETES_SERVICE_HOST"] = "True"

    package.is_docker_env.cache_clear()
    with (
        patch("homeassistant.util.package.Path", side_effect=new_path_mock),
        patch(
            "homeassistant.util.package.is_official_image",
            return_value=is_official_image,
        ),
        patch.dict(os.environ, env),
    ):
        expect(package.is_docker_env()).to_be(
            any([dockerenv, containerenv, kubernetes_service_host, is_official_image])
        )


@test.cases(
    test.case(
        "official_image-kubernetes-containerenv-dockerenv",
        dockerenv=True,
        containerenv=True,
        kubernetes_service_host=True,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-kubernetes-containerenv-dockerenv",
        dockerenv=True,
        containerenv=True,
        kubernetes_service_host=True,
        is_official_image=False,
    ),
    test.case(
        "official_image-not_kubernetes-containerenv-dockerenv",
        dockerenv=True,
        containerenv=True,
        kubernetes_service_host=False,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-not_kubernetes-containerenv-dockerenv",
        dockerenv=True,
        containerenv=True,
        kubernetes_service_host=False,
        is_official_image=False,
    ),
    test.case(
        "official_image-kubernetes-not_containerenv-dockerenv",
        dockerenv=True,
        containerenv=False,
        kubernetes_service_host=True,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-kubernetes-not_containerenv-dockerenv",
        dockerenv=True,
        containerenv=False,
        kubernetes_service_host=True,
        is_official_image=False,
    ),
    test.case(
        "official_image-not_kubernetes-not_containerenv-dockerenv",
        dockerenv=True,
        containerenv=False,
        kubernetes_service_host=False,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-not_kubernetes-not_containerenv-dockerenv",
        dockerenv=True,
        containerenv=False,
        kubernetes_service_host=False,
        is_official_image=False,
    ),
    test.case(
        "official_image-kubernetes-containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=True,
        kubernetes_service_host=True,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-kubernetes-containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=True,
        kubernetes_service_host=True,
        is_official_image=False,
    ),
    test.case(
        "official_image-not_kubernetes-containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=True,
        kubernetes_service_host=False,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-not_kubernetes-containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=True,
        kubernetes_service_host=False,
        is_official_image=False,
    ),
    test.case(
        "official_image-kubernetes-not_containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=False,
        kubernetes_service_host=True,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-kubernetes-not_containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=False,
        kubernetes_service_host=True,
        is_official_image=False,
    ),
    test.case(
        "official_image-not_kubernetes-not_containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=False,
        kubernetes_service_host=False,
        is_official_image=True,
    ),
    test.case(
        "not_official_image-not_kubernetes-not_containerenv-not_dockerenv",
        dockerenv=False,
        containerenv=False,
        kubernetes_service_host=False,
        is_official_image=False,
    ),
)
async def is_docker_env(
    dockerenv: bool,
    containerenv: bool,
    kubernetes_service_host: bool,
    is_official_image: bool,
) -> None:
    """Test is_docker_env."""
    await _run_is_docker_env(
        dockerenv, containerenv, kubernetes_service_host, is_official_image
    )
