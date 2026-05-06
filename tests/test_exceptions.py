"""Test to verify that Home Assistant exceptions work."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConditionErrorContainer,
    ConditionErrorIndex,
    ConditionErrorMessage,
    HomeAssistantError,
    TemplateError,
)

from .hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def conditionerror_format() -> None:
    """Test ConditionError stringifiers."""
    error1 = ConditionErrorMessage("test", "A test error")
    expect(str(error1)).to_equal("In 'test' condition: A test error")

    error2 = ConditionErrorMessage("test", "Another error")
    expect(str(error2)).to_equal("In 'test' condition: Another error")

    error_pos1 = ConditionErrorIndex("box", index=0, total=2, error=error1)
    expect(str(error_pos1)).to_equal(
        """In 'box' (item 1 of 2):
  In 'test' condition: A test error"""
    )

    error_pos2 = ConditionErrorIndex("box", index=1, total=2, error=error2)
    expect(str(error_pos2)).to_equal(
        """In 'box' (item 2 of 2):
  In 'test' condition: Another error"""
    )

    error_container1 = ConditionErrorContainer("box", errors=[error_pos1, error_pos2])
    expect(str(error_container1)).to_equal(
        """In 'box' (item 1 of 2):
  In 'test' condition: A test error
In 'box' (item 2 of 2):
  In 'test' condition: Another error"""
    )

    error_pos3 = ConditionErrorIndex("box", index=0, total=1, error=error1)
    expect(str(error_pos3)).to_equal(
        """In 'box':
  In 'test' condition: A test error"""
    )


@test.cases(
    test.case("str", arg="message", expected="message"),
    test.case("exception", arg=Exception("message"), expected="Exception: message"),
)
def template_message(arg: str | Exception, expected: str) -> None:
    """Ensure we can create TemplateError."""
    template_error = TemplateError(arg)
    expect(str(template_error)).to_equal(expected)


_type_error_bla = TypeError("bla")


def _raise_ha_error(args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
    raise HomeAssistantError(*args, **kwargs)


def _raise(exc: BaseException) -> None:
    raise exc


@test.cases(
    test.case(
        "no_args",
        exception_args=(),
        exception_kwargs={},
        args_base_class=(),
        message="",
    ),
    test.case(
        "single_str",
        exception_args=("bla",),
        exception_kwargs={},
        args_base_class=("bla",),
        message="bla",
    ),
    test.case(
        "none",
        exception_args=(None,),
        exception_kwargs={},
        args_base_class=(None,),
        message="None",
    ),
    test.case(
        "type_error",
        exception_args=(_type_error_bla,),
        exception_kwargs={},
        args_base_class=(_type_error_bla,),
        message="bla",
    ),
    test.case(
        "missing_translation",
        exception_args=(),
        exception_kwargs={"translation_domain": "test", "translation_key": "test"},
        args_base_class=("test",),
        message="test",
    ),
    test.case(
        "cached_translation",
        exception_args=(),
        exception_kwargs={"translation_domain": "test", "translation_key": "bla"},
        args_base_class=("bla",),
        message="{bla} from cache",
    ),
    test.case(
        "cached_translation_placeholders",
        exception_args=(),
        exception_kwargs={
            "translation_domain": "test",
            "translation_key": "bla",
            "translation_placeholders": {"bla": "Bla"},
        },
        args_base_class=("bla",),
        message="Bla from cache",
    ),
)
async def home_assistant_error(
    exception_args: tuple[Any, ...],
    exception_kwargs: dict[str, Any],
    args_base_class: tuple[Any],
    message: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test edge cases with HomeAssistantError."""
    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={"component.test.exceptions.bla.message": "{bla} from cache"},
    ):
        try:
            _raise_ha_error(exception_args, exception_kwargs)
        except HomeAssistantError as exc:
            expect(exc.args).to_equal(args_base_class)
            expect(str(exc)).to_equal(message)
            expect(str(exc)).to_equal(message)
        else:
            raise AssertionError("Expected HomeAssistantError")


@test
async def home_assistant_error_subclass(hass: HomeAssistant = Depends(hass)) -> None:
    """Test __str__ method on an HomeAssistantError subclass."""

    class _SubExceptionDefault(HomeAssistantError):
        """Sub class, default with generated message."""

    class _SubExceptionConstructor(HomeAssistantError):
        """Sub class with constructor, no generated message."""

        def __init__(
            self,
            custom_arg: str,
            translation_domain: str | None = None,
            translation_key: str | None = None,
            translation_placeholders: dict[str, str] | None = None,
        ) -> None:
            super().__init__(
                translation_domain=translation_domain,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            self.custom_arg = custom_arg

    class _SubExceptionConstructorGenerate(HomeAssistantError):
        """Sub class with constructor, with generated message."""

        generate_message: bool = True

        def __init__(
            self,
            custom_arg: str,
            translation_domain: str | None = None,
            translation_key: str | None = None,
            translation_placeholders: dict[str, str] | None = None,
        ) -> None:
            super().__init__(
                translation_domain=translation_domain,
                translation_key=translation_key,
                translation_placeholders=translation_placeholders,
            )
            self.custom_arg = custom_arg

    class _SubExceptionGenerate(HomeAssistantError):
        """Sub class, no generated message."""

        generate_message: bool = True

    class _SubClassWithExceptionGroup(HomeAssistantError, BaseExceptionGroup):
        """Sub class with exception group, no generated message."""

    class _SubClassWithExceptionGroupGenerate(HomeAssistantError, BaseExceptionGroup):
        """Sub class with exception group and generated message."""

        generate_message: bool = True

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={"component.test.exceptions.bla.message": "{bla} from cache"},
    ):
        # A subclass without a constructor generates a message by default
        try:
            _raise(
                _SubExceptionDefault(
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("Bla from cache")

        # Constructor that does not pass args to super class
        try:
            _raise(
                _SubExceptionConstructor(
                    "custom arg",
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("Bla from cache")
        try:
            _raise(_SubExceptionConstructor("custom arg"))
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("")

        # Constructor that generates the message
        try:
            _raise(
                _SubExceptionConstructorGenerate(
                    "custom arg",
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("Bla from cache")

        # No overridden constructor; passed args override translation
        try:
            _raise(
                _SubExceptionDefault(
                    ValueError("wrong value"),
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("wrong value")

        # generate_message = True forces message generation
        try:
            _raise(
                _SubExceptionGenerate(
                    ValueError("wrong value"),
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("Bla from cache")

        # ExceptionGroup subclass, generated message disabled
        try:
            _raise(
                _SubClassWithExceptionGroup(
                    "group message",
                    [ValueError("wrong value"), TypeError("wrong type")],
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("group message (2 sub-exceptions)")
        try:
            _raise(
                _SubClassWithExceptionGroup(
                    "group message",
                    [ValueError("wrong value"), TypeError("wrong type")],
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("group message (2 sub-exceptions)")

        # ExceptionGroup subclass with generated message enabled
        try:
            _raise(
                _SubClassWithExceptionGroupGenerate(
                    "group message",
                    [ValueError("wrong value"), TypeError("wrong type")],
                    translation_domain="test",
                    translation_key="bla",
                    translation_placeholders={"bla": "Bla"},
                )
            )
        except HomeAssistantError as exc:
            expect(str(exc)).to_equal("Bla from cache")
