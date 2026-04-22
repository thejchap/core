"""Tests for pylint hass_enforce_type_hints plugin."""

from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import UNDEFINED
from pylint.testutils import MessageTest
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, fixture, test

from . import assert_adds_messages, assert_no_messages
from .fixtures import decorator_checker, linter


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def good_callback(
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test good `@callback` decorator."""
    code = """
    from homeassistant.core import callback

    @callback
    def setup(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test
def bad_callback(
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test bad `@callback` decorator."""
    code = """
    from homeassistant.core import callback

    @callback
    async def setup(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-async-callback-decorator",
            line=5,
            node=root_node.body[1],
            args=None,
            confidence=UNDEFINED,
            col_offset=0,
            end_line=5,
            end_col_offset=15,
        ),
    ):
        walker.walk(root_node)


@test.cases(
    test.case("function_bootstrap", keywords='scope="function"', path="tests.test_bootstrap"),
    test.case("class_bootstrap", keywords='scope="class"', path="tests.test_bootstrap"),
    test.case("module_bootstrap", keywords='scope="module"', path="tests.test_bootstrap"),
    test.case("package_bootstrap", keywords='scope="package"', path="tests.test_bootstrap"),
    test.case(
        "session_autouse_bootstrap",
        keywords='scope="session", autouse=True',
        path="tests.test_bootstrap",
    ),
    test.case(
        "function_components_conftest",
        keywords='scope="function"',
        path="tests.components.conftest",
    ),
    test.case(
        "class_components_conftest",
        keywords='scope="class"',
        path="tests.components.conftest",
    ),
    test.case(
        "module_components_conftest",
        keywords='scope="module"',
        path="tests.components.conftest",
    ),
    test.case(
        "package_components_conftest",
        keywords='scope="package"',
        path="tests.components.conftest",
    ),
    test.case(
        "session_autouse_components_conftest",
        keywords='scope="session", autouse=True',
        path="tests.components.conftest",
    ),
    test.case(
        "session_autouse_findspec_components_conftest",
        keywords='scope="session", autouse=find_spec("zeroconf") is not None',
        path="tests.components.conftest",
    ),
    test.case(
        "function_pylint_tests_conftest",
        keywords='scope="function"',
        path="tests.components.pylint_tests.conftest",
    ),
    test.case(
        "class_pylint_tests_conftest",
        keywords='scope="class"',
        path="tests.components.pylint_tests.conftest",
    ),
    test.case(
        "module_pylint_tests_conftest",
        keywords='scope="module"',
        path="tests.components.pylint_tests.conftest",
    ),
    test.case(
        "package_pylint_tests_conftest",
        keywords='scope="package"',
        path="tests.components.pylint_tests.conftest",
    ),
    test.case(
        "function_pylint_test",
        keywords='scope="function"',
        path="tests.components.pylint_test",
    ),
    test.case(
        "class_pylint_test",
        keywords='scope="class"',
        path="tests.components.pylint_test",
    ),
    test.case(
        "module_pylint_test",
        keywords='scope="module"',
        path="tests.components.pylint_test",
    ),
)
def good_fixture(
    keywords: str,
    path: str,
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test good `@pytest.fixture` decorator."""
    code = f"""
    import pytest

    @pytest.fixture
    def setup(
        arg1, arg2
    ):
        pass

    @pytest.fixture({keywords})
    def setup_session(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case("pylint_test", path="tests.components.pylint_test"),
    test.case("pylint_test_conftest", path="tests.components.pylint_test.conftest"),
    test.case("pylint_test_module", path="tests.components.pylint_test.module"),
)
def bad_fixture_session_scope(
    path: str,
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test bad `@pytest.fixture` decorator."""
    code = """
    import pytest

    @pytest.fixture
    def setup(
        arg1, arg2
    ):
        pass

    @pytest.fixture(scope="session")
    def setup_session(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-pytest-fixture-decorator",
            line=10,
            node=root_node.body[2].decorators.nodes[0],
            args=("scope `session`", "use `package` or lower"),
            confidence=UNDEFINED,
            col_offset=1,
            end_line=10,
            end_col_offset=32,
        ),
    ):
        walker.walk(root_node)


@test.cases(
    test.case("pylint_test", path="tests.components.pylint_test"),
    test.case("pylint_test_module", path="tests.components.pylint_test.module"),
)
def bad_fixture_package_scope(
    path: str,
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test bad `@pytest.fixture` decorator."""
    code = """
    import pytest

    @pytest.fixture
    def setup(
        arg1, arg2
    ):
        pass

    @pytest.fixture(scope="package")
    def setup_session(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-pytest-fixture-decorator",
            line=10,
            node=root_node.body[2].decorators.nodes[0],
            args=("scope `package`", "use `module` or lower"),
            confidence=UNDEFINED,
            col_offset=1,
            end_line=10,
            end_col_offset=32,
        ),
    ):
        walker.walk(root_node)


@test.cases(
    test.case(
        "session_bootstrap",
        keywords='scope="session"',
        path="tests.test_bootstrap",
    ),
    test.case(
        "session_autouse_false_bootstrap",
        keywords='scope="session", autouse=False',
        path="tests.test_bootstrap",
    ),
    test.case(
        "session_components_conftest",
        keywords='scope="session"',
        path="tests.components.conftest",
    ),
    test.case(
        "session_autouse_false_components_conftest",
        keywords='scope="session", autouse=False',
        path="tests.components.conftest",
    ),
)
def bad_fixture_autouse(
    keywords: str,
    path: str,
    linter: UnittestLinter = Depends(linter),
    decorator_checker: BaseChecker = Depends(decorator_checker),
) -> None:
    """Test bad `@pytest.fixture` decorator."""
    code = f"""
    import pytest

    @pytest.fixture
    def setup(
        arg1, arg2
    ):
        pass

    @pytest.fixture({keywords})
    def setup_session(
        arg1, arg2
    ):
        pass
    """

    root_node = astroid.parse(code, path)
    walker = ASTWalker(linter)
    walker.add_checker(decorator_checker)

    with assert_adds_messages(
        linter,
        MessageTest(
            msg_id="hass-pytest-fixture-decorator",
            line=10,
            node=root_node.body[2].decorators.nodes[0],
            args=("scope/autouse combination", "set `autouse=True` or reduce scope"),
            confidence=UNDEFINED,
            col_offset=1,
            end_line=10,
            end_col_offset=17 + len(keywords),
        ),
    ):
        walker.walk(root_node)
