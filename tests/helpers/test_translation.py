"""Test the translation helper."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
import contextlib
import pathlib
from typing import Any
from unittest.mock import Mock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import caplog, hass  # noqa: F401


def _enable_custom_integrations(hass: HomeAssistant) -> None:
    """Enable custom integrations defined in the test dir.

    Ported from the pytest ``enable_custom_integrations`` fixture in
    ``tests/conftest.py`` — Tryke's module-level fixtures auto-apply so this
    must stay opt-in per test.
    """
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)


@contextlib.contextmanager
def _mock_config_flows() -> Generator[dict[str, Any]]:
    """Patch ``loader.FLOWS`` with an empty dict for the duration of a test."""
    flows: dict[str, Any] = {"integration": [], "helper": {}}
    with patch.object(loader, "FLOWS", flows):
        yield flows


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def recursive_flatten() -> None:
    """Test the flatten function."""
    data = {"parent1": {"child1": "data1", "child2": "data2"}, "parent2": "data3"}

    flattened = translation.recursive_flatten("prefix.", data)

    expect(flattened).to_equal(
        {
            "prefix.parent1.child1": "data1",
            "prefix.parent1.child2": "data2",
            "prefix.parent2": "data3",
        }
    )


@test
async def load_translations_files_by_language(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test the load translation files function."""
    en_file = hass.config.path("custom_components", "test", "translations", "en.json")
    invalid_file = hass.config.path(
        "custom_components", "test", "translations", "invalid.json"
    )
    broken_file = hass.config.path(
        "custom_components", "test", "translations", "_broken.json"
    )
    expect(
        translation._load_translations_files_by_language(
            {
                "en": {"test": en_file},
                "invalid": {"test": invalid_file},
                "broken": {"test": broken_file},
            }
        )
    ).to_equal(
        {
            "broken": {},
            "en": {
                "test": {
                    "entity": {
                        "switch": {
                            "other1": {
                                "name": "Other 1",
                                "unit_of_measurement": "units",
                            },
                            "other2": {"name": "Other 2"},
                            "other3": {"name": "Other 3"},
                            "other4": {
                                "name": "Other 4",
                                "unit_of_measurement": "quantities",
                            },
                            "outlet": {"name": "Outlet {placeholder}"},
                        }
                    },
                    "something": "else",
                }
            },
            "invalid": {"test": {}},
        }
    )
    expect(caplog.text).to_contain("Translation file is unexpected type")
    expect(caplog.text).to_contain("_broken.json")


@test.cases(
    test.case(
        "en",
        language="en",
        expected_translation={
            "component.test.entity.switch.other1.name": "Other 1",
            "component.test.entity.switch.other1.unit_of_measurement": "units",
            "component.test.entity.switch.other2.name": "Other 2",
            "component.test.entity.switch.other3.name": "Other 3",
            "component.test.entity.switch.other4.name": "Other 4",
            "component.test.entity.switch.other4.unit_of_measurement": "quantities",
            "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
        },
        expected_errors=[],
    ),
    test.case(
        "es",
        language="es",
        expected_translation={
            "component.test.entity.switch.other1.name": "Otra 1",
            "component.test.entity.switch.other1.unit_of_measurement": "units",
            "component.test.entity.switch.other2.name": "Otra 2",
            "component.test.entity.switch.other3.name": "Otra 3",
            "component.test.entity.switch.other4.name": "Otra 4",
            "component.test.entity.switch.other4.unit_of_measurement": "quantities",
            "component.test.entity.switch.outlet.name": "Enchufe {placeholder}",
        },
        expected_errors=[],
    ),
    test.case(
        "de",
        language="de",
        expected_translation={
            "component.test.entity.switch.other1.name": "Anderes 1",
            "component.test.entity.switch.other1.unit_of_measurement": "einheiten",
            "component.test.entity.switch.other2.name": "Other 2",
            "component.test.entity.switch.other3.name": "",
            "component.test.entity.switch.other4.name": "Other 4",
            "component.test.entity.switch.other4.unit_of_measurement": "quantities",
            "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
        },
        expected_errors=[
            "component.test.entity.switch.other2.name",
            "component.test.entity.switch.outlet.name",
        ],
    ),
)
async def load_translations_files_invalid_localized_placeholders(
    language: str,
    expected_translation: dict[str, str],
    expected_errors: list[str],
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test the load translation files with invalid localized placeholders."""
    _enable_custom_integrations(hass)
    caplog.clear()
    translations = await translation.async_get_translations(
        hass, language, "entity", ["test"]
    )
    expect(translations).to_equal(expected_translation)

    expect(
        ("Validation of translation placeholders" in caplog.text)
        == (len(expected_errors) > 0)
    ).to_be(True)
    for expected_error in expected_errors:
        expect(caplog.text).to_contain(
            f"Validation of translation placeholders for localized ({language}) "
            f"string {expected_error} failed"
        )


@test
async def get_translations(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the get translations helper."""
    _enable_custom_integrations(hass)
    with _mock_config_flows():
        translations = await translation.async_get_translations(hass, "en", "entity")
        expect(translations).to_equal({})

        expect(
            await async_setup_component(hass, "switch", {"switch": {"platform": "test"}})
        ).to_be(True)
        await hass.async_block_till_done()

        translations = await translation.async_get_translations(
            hass, "en", "entity", {"test"}
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Other 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Other 2",
                "component.test.entity.switch.other3.name": "Other 3",
                "component.test.entity.switch.other4.name": "Other 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
            }
        )

        translations = await translation.async_get_translations(
            hass, "de", "entity", {"test"}
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Anderes 1",
                "component.test.entity.switch.other1.unit_of_measurement": "einheiten",
                "component.test.entity.switch.other2.name": "Other 2",
                "component.test.entity.switch.other3.name": "",
                "component.test.entity.switch.other4.name": "Other 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
            }
        )

        translations = await translation.async_get_translations(
            hass, "es", "entity", {"test"}
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Otra 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Otra 2",
                "component.test.entity.switch.other3.name": "Otra 3",
                "component.test.entity.switch.other4.name": "Otra 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Enchufe {placeholder}",
            }
        )

        translations = await translation.async_get_translations(
            hass, "invalid-language", "entity", {"test"}
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Other 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Other 2",
                "component.test.entity.switch.other3.name": "Other 3",
                "component.test.entity.switch.other4.name": "Other 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
            }
        )


@test
async def get_translations_loads_config_flows(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the get translations helper loads config flow translations."""
    with _mock_config_flows() as mock_config_flows:
        mock_config_flows["integration"].append("component1")
        integration = Mock(file_path=pathlib.Path(__file__))
        integration.name = "Component 1"

        with (
            patch(
                "homeassistant.helpers.translation._load_translations_files_by_language",
                return_value={"en": {"component1": {"title": "world"}}},
            ),
            patch(
                "homeassistant.helpers.translation.async_get_integrations",
                return_value={"component1": integration},
            ),
        ):
            translations = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )
            translations_again = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )

            expect(translations).to_equal(translations_again)

        expect(translations).to_equal({"component.component1.title": "world"})

        expect("component1" not in hass.config.components).to_be(True)

        mock_config_flows["integration"].append("component2")
        integration = Mock(file_path=pathlib.Path(__file__))
        integration.name = "Component 2"

        with (
            patch(
                "homeassistant.helpers.translation._load_translations_files_by_language",
                return_value={"en": {"component2": {"title": "world"}}},
            ),
            patch(
                "homeassistant.helpers.translation.async_get_integrations",
                return_value={"component2": integration},
            ),
        ):
            translations = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )
            translations_again = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )

            expect(translations).to_equal(translations_again)

        expect(translations).to_equal(
            {
                "component.component1.title": "world",
                "component.component2.title": "world",
            }
        )

        translations_all_cached = await translation.async_get_translations(
            hass, "en", "title", config_flow=True
        )
        expect(translations).to_equal(translations_all_cached)

        expect("component1" not in hass.config.components).to_be(True)
        expect("component2" not in hass.config.components).to_be(True)


@test
async def get_translations_while_loading_components(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the get translations helper loads config flow translations."""
    integration = Mock(file_path=pathlib.Path(__file__))
    integration.name = "Component 1"
    hass.config.components.add("component1")
    load_count = 0

    def mock_load_translation_files(
        files: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Mock load translation files."""
        nonlocal load_count
        load_count += 1
        return {language: {"component1": {"title": "world"}} for language in files}

    with (
        patch(
            "homeassistant.helpers.translation._load_translations_files_by_language",
            mock_load_translation_files,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_integrations",
            return_value={"component1": integration},
        ),
    ):
        tasks = [
            translation.async_get_translations(hass, "en", "title") for _ in range(5)
        ]
        all_translations = await asyncio.gather(*tasks)

    expect(all_translations[0]).to_equal({"component.component1.title": "world"})
    expect(load_count).to_equal(1)


@test.xfail(
    "HA's session-scoped translations_once cache from tests/conftest.py "
    "cannot be replicated under Tryke's per-test hass lifecycle."
)
async def get_translation_categories(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the get translations helper loads config flow translations."""
    with patch.object(translation, "async_get_config_flows", return_value={"light"}):
        translations = await translation.async_get_translations(
            hass, "en", "title", None, True
        )
        expect("component.light.title" in translations).to_be(True)

        translations = await translation.async_get_translations(
            hass, "en", "device_automation", None, True
        )
        expect(
            "component.light.device_automation.action_type.turn_on" in translations
        ).to_be(True)


@test
async def translation_merging_loaded_together(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test we merge translations of two integrations when they are loaded at the same time."""
    hass.config.components.add("hue")
    hass.config.components.add("homekit")
    hue_translations = await translation.async_get_translations(
        hass, "en", "config", integrations={"hue"}
    )
    homekit_translations = await translation.async_get_translations(
        hass, "en", "config", integrations={"homekit"}
    )

    translations = await translation.async_get_translations(
        hass, "en", "config", integrations={"hue", "homekit"}
    )
    expect(translations).to_equal(hue_translations | homekit_translations)


@test.xfail(
    "HA's session-scoped translations_once cache from tests/conftest.py "
    "cannot be replicated under Tryke's per-test hass lifecycle."
)
async def ensure_translations_still_load_if_one_integration_fails(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test that if one integration fails to load we can still get translations."""
    hass.config.components.add("sensor")
    hass.config.components.add("broken")

    sensor_integration = await loader.async_get_integration(hass, "sensor")

    with patch(
        "homeassistant.helpers.translation.async_get_integrations",
        return_value={
            "sensor": sensor_integration,
            "broken": Exception("unhandled failure"),
        },
    ):
        translations = await translation.async_get_translations(
            hass, "en", "entity_component", integrations={"sensor", "broken"}
        )
        expect(caplog.text).to_contain("Failed to load integration for translation")
        expect(caplog.text).to_contain("broken")

    expect(bool(translations)).to_be(True)

    sensor_translations = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"sensor"}
    )

    expect(translations).to_equal(sensor_translations)


@test
async def load_translations_all_integrations_broken(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Ensure we do not try to load translations again if the integration is broken."""
    hass.config.components.add("broken")
    hass.config.components.add("broken2")

    with patch(
        "homeassistant.helpers.translation.async_get_integrations",
        return_value={
            "broken2": Exception("unhandled failure"),
            "broken": Exception("unhandled failure"),
        },
    ):
        translations = await translation.async_get_translations(
            hass, "en", "entity_component", integrations={"broken", "broken2"}
        )
    expect(caplog.text).to_contain("Failed to load integration for translation")
    expect(caplog.text).to_contain("broken")
    expect(caplog.text).to_contain("broken2")
    expect(not translations).to_be(True)
    caplog.clear()

    translations = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"broken", "broken2"}
    )
    expect(not translations).to_be(True)
    expect(
        "Failed to load integration for translation" not in caplog.text
    ).to_be(True)


@test.xfail(
    "HA's session-scoped translations_once cache from tests/conftest.py "
    "cannot be replicated under Tryke's per-test hass lifecycle."
)
async def caching(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we cache data."""
    hass.config.components.add("sensor")
    hass.config.components.add("light")

    with patch(
        "homeassistant.helpers.translation.build_resources",
        side_effect=translation.build_resources,
    ) as mock_build_resources:
        load1 = await translation.async_get_translations(hass, "en", "entity_component")
        expect(len(mock_build_resources.mock_calls)).to_equal(9)

        load2 = await translation.async_get_translations(hass, "en", "entity_component")
        expect(len(mock_build_resources.mock_calls)).to_equal(9)

        expect(load1).to_equal(load2)

        for key in load1:
            expect(
                key.startswith(
                    (
                        "component.sensor.entity_component.",
                        "component.light.entity_component.",
                    )
                )
            ).to_be(True)

    load_sensor_only = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"sensor"}
    )
    expect(bool(load_sensor_only)).to_be(True)
    for key in load_sensor_only:
        expect(key.startswith("component.sensor.entity_component.")).to_be(True)

    load_light_only = await translation.async_get_translations(
        hass, "en", "entity_component", integrations={"light"}
    )
    expect(bool(load_light_only)).to_be(True)
    for key in load_light_only:
        expect(key.startswith("component.light.entity_component.")).to_be(True)

    hass.config.components.add("media_player")

    with patch(
        "homeassistant.helpers.translation.build_resources",
        side_effect=translation.build_resources,
    ) as mock_build:
        load_sensor_only = await translation.async_get_translations(
            hass, "en", "title", integrations={"sensor"}
        )
        expect(bool(load_sensor_only)).to_be(True)
        for key in load_sensor_only:
            expect(key).to_equal("component.sensor.title")
        expect(len(mock_build.mock_calls)).to_equal(0)

        expect(
            bool(
                await translation.async_get_translations(
                    hass, "en", "title", integrations={"sensor"}
                )
            )
        ).to_be(True)
        expect(len(mock_build.mock_calls)).to_equal(0)

        load_light_only = await translation.async_get_translations(
            hass, "en", "title", integrations={"media_player"}
        )
        expect(bool(load_light_only)).to_be(True)
        for key in load_light_only:
            expect(key).to_equal("component.media_player.title")
        expect(len(mock_build.mock_calls) > 1).to_be(True)


@test
async def custom_component_translations(hass: HomeAssistant = Depends(hass)) -> None:
    """Test getting translation from custom components."""
    _enable_custom_integrations(hass)
    hass.config.components.add("test_embedded")
    hass.config.components.add("test_package")
    expect(await translation.async_get_translations(hass, "en", "state")).to_equal({})


@test
async def get_cached_translations(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the get cached translations helper."""
    _enable_custom_integrations(hass)
    with _mock_config_flows():
        translations = await translation.async_get_translations(hass, "en", "entity")
        expect(translations).to_equal({})

        expect(
            await async_setup_component(hass, "switch", {"switch": {"platform": "test"}})
        ).to_be(True)
        await hass.async_block_till_done()

        await translation._async_get_translations_cache(hass).async_load(
            "en", {"test"}
        )

        translations = translation.async_get_cached_translations(
            hass, "en", "entity", "test"
        )
        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Other 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Other 2",
                "component.test.entity.switch.other3.name": "Other 3",
                "component.test.entity.switch.other4.name": "Other 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
            }
        )

        await translation._async_get_translations_cache(hass).async_load(
            "es", {"test"}
        )

        translations = translation.async_get_cached_translations(
            hass, "es", "entity", "test"
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Otra 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Otra 2",
                "component.test.entity.switch.other3.name": "Otra 3",
                "component.test.entity.switch.other4.name": "Otra 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Enchufe {placeholder}",
            }
        )

        await translation._async_get_translations_cache(hass).async_load(
            "invalid-language", {"test"}
        )

        translations = translation.async_get_cached_translations(
            hass, "invalid-language", "entity", "test"
        )

        expect(translations).to_equal(
            {
                "component.test.entity.switch.other1.name": "Other 1",
                "component.test.entity.switch.other1.unit_of_measurement": "units",
                "component.test.entity.switch.other2.name": "Other 2",
                "component.test.entity.switch.other3.name": "Other 3",
                "component.test.entity.switch.other4.name": "Other 4",
                "component.test.entity.switch.other4.unit_of_measurement": "quantities",
                "component.test.entity.switch.outlet.name": "Outlet {placeholder}",
            }
        )


@test
async def setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the setup load listeners helper."""
    translation.async_setup(hass)

    with patch(
        "homeassistant.helpers.translation._TranslationCache.async_load",
    ) as mock:
        hass.bus.async_fire(EVENT_CORE_CONFIG_UPDATE, {"language": "en"})
        await hass.async_block_till_done()
        mock.assert_not_called()

    with patch(
        "homeassistant.helpers.translation._TranslationCache.async_load",
    ) as mock:
        hass.bus.async_fire(EVENT_CORE_CONFIG_UPDATE, {"language": "es"})
        await hass.async_block_till_done()
        mock.assert_called_once_with("es", set())

    with patch(
        "homeassistant.helpers.translation._TranslationCache.async_load",
    ) as mock:
        hass.bus.async_fire(EVENT_CORE_CONFIG_UPDATE, {})
        await hass.async_block_till_done()
        mock.assert_not_called()


@test
async def translate_state(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the state translation helper."""
    result = translation.async_translate_state(
        hass, "unavailable", "binary_sensor", "platform", "translation_key", None
    )
    expect(result).to_equal("unavailable")

    result = translation.async_translate_state(
        hass, "unknown", "binary_sensor", "platform", "translation_key", None
    )
    expect(result).to_equal("unknown")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.platform.entity.binary_sensor.translation_key.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", "translation_key", None
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.binary_sensor.entity_component.device_class.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, "device_class"
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.binary_sensor.entity_component._.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, None
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, None
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        expect(result).to_equal("on")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", "translation_key", "device_class"
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity"),
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        expect(result).to_equal("on")


@test
async def translate_state_attr(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the state attribute translation helper."""
    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.platform.entity.climate.translation_key.state_attributes.fan_mode.state.auto": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state_attr(
            hass,
            "auto",
            "climate",
            "platform",
            "translation_key",
            None,
            "fan_mode",
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.climate.entity_component.device_class.state_attributes.fan_mode.state.auto": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state_attr(
            hass,
            "auto",
            "climate",
            "platform",
            None,
            "device_class",
            "fan_mode",
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.climate.entity_component._.state_attributes.fan_mode.state.auto": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state_attr(
            hass, "auto", "climate", "platform", None, None, "fan_mode"
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        expect(result).to_equal("TRANSLATED")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state_attr(
            hass, "auto", "climate", "platform", None, None, "fan_mode"
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        expect(result).to_equal("auto")

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state_attr(
            hass,
            "auto",
            "climate",
            "platform",
            "translation_key",
            "device_class",
            "fan_mode",
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity"),
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        expect(result).to_equal("auto")


@test
async def get_translations_still_has_title_without_translations_files(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the title still gets added in if there are no translation files."""
    with _mock_config_flows() as mock_config_flows:
        mock_config_flows["integration"].append("component1")
        integration = Mock(file_path=pathlib.Path(__file__))
        integration.name = "Component 1"

        with (
            patch(
                "homeassistant.helpers.translation._load_translations_files_by_language",
                return_value={},
            ),
            patch(
                "homeassistant.helpers.translation.async_get_integrations",
                return_value={"component1": integration},
            ),
        ):
            translations = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )
            translations_again = await translation.async_get_translations(
                hass, "en", "title", config_flow=True
            )

            expect(translations).to_equal(translations_again)
    expect(translations).to_equal({"component.component1.title": "Component 1"})
