"""The tests for the microsoft face platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import camera, microsoft_face as mf
from homeassistant.components.microsoft_face import (
    ATTR_CAMERA_ENTITY,
    ATTR_GROUP,
    ATTR_PERSON,
    DOMAIN,
    SERVICE_CREATE_GROUP,
    SERVICE_CREATE_PERSON,
    SERVICE_DELETE_GROUP,
    SERVICE_DELETE_PERSON,
    SERVICE_FACE_PERSON,
    SERVICE_TRAIN_GROUP,
)
from homeassistant.const import ATTR_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component, async_load_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


def _patch_update_store():
    """Context manager that mocks ``MicrosoftFace.update_store``."""
    return patch(
        "homeassistant.components.microsoft_face.MicrosoftFace.update_store",
        return_value=None,
    )


def create_group(hass: HomeAssistant, name: str) -> None:
    """Create a new person group."""
    data = {ATTR_NAME: name}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_CREATE_GROUP, data))


def delete_group(hass: HomeAssistant, name: str) -> None:
    """Delete a person group."""
    data = {ATTR_NAME: name}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_DELETE_GROUP, data))


def train_group(hass: HomeAssistant, group: str) -> None:
    """Train a person group."""
    data = {ATTR_GROUP: group}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_TRAIN_GROUP, data))


def create_person(hass: HomeAssistant, group: str, name: str) -> None:
    """Create a person in a group."""
    data = {ATTR_GROUP: group, ATTR_NAME: name}
    hass.async_create_task(
        hass.services.async_call(DOMAIN, SERVICE_CREATE_PERSON, data)
    )


def delete_person(hass: HomeAssistant, group: str, name: str) -> None:
    """Delete a person in a group."""
    data = {ATTR_GROUP: group, ATTR_NAME: name}
    hass.async_create_task(
        hass.services.async_call(DOMAIN, SERVICE_DELETE_PERSON, data)
    )


def face_person(
    hass: HomeAssistant, group: str, person: str, camera_entity: str
) -> None:
    """Add a new face picture to a person."""
    data = {ATTR_GROUP: group, ATTR_PERSON: person, ATTR_CAMERA_ENTITY: camera_entity}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_FACE_PERSON, data))


CONFIG = {mf.DOMAIN: {"api_key": "12345678abcdef"}}
ENDPOINT_URL = f"https://westus.{mf.FACE_API_URL}"


@test
async def test_setup_component(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up component."""
    await async_setup_component(hass, "homeassistant", {})
    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)


@test
async def test_setup_component_wrong_api_key(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up component without api key."""
    await async_setup_component(hass, "homeassistant", {})
    with _patch_update_store(), assert_setup_component(0, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, {mf.DOMAIN: {}})


@test
async def test_setup_component_test_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up component."""
    await async_setup_component(hass, "homeassistant", {})
    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    expect(hass.services.has_service(mf.DOMAIN, "create_group")).to_be_truthy()
    expect(hass.services.has_service(mf.DOMAIN, "delete_group")).to_be_truthy()
    expect(hass.services.has_service(mf.DOMAIN, "train_group")).to_be_truthy()
    expect(hass.services.has_service(mf.DOMAIN, "create_person")).to_be_truthy()
    expect(hass.services.has_service(mf.DOMAIN, "delete_person")).to_be_truthy()
    expect(hass.services.has_service(mf.DOMAIN, "face_person")).to_be_truthy()


@test
async def test_setup_component_test_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups"),
        text=await async_load_fixture(hass, "persongroups.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group2/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )

    with assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(3)

    entity_group1 = hass.states.get("microsoft_face.test_group1")
    entity_group2 = hass.states.get("microsoft_face.test_group2")

    expect(entity_group1).not_.to_be_none().fatal()
    expect(entity_group2).not_.to_be_none().fatal()

    expect(entity_group1.attributes["Ryan"]).to_equal(
        "25985303-c537-4467-b41d-bdb45cd95ca1"
    )
    expect(entity_group1.attributes["David"]).to_equal(
        "2ae4935b-9659-44c3-977f-61fac20d0538"
    )

    expect(entity_group2.attributes["Ryan"]).to_equal(
        "25985303-c537-4467-b41d-bdb45cd95ca1"
    )
    expect(entity_group2.attributes["David"]).to_equal(
        "2ae4935b-9659-44c3-977f-61fac20d0538"
    )


@test
async def test_service_groups(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test groups services."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.put(
        ENDPOINT_URL.format("persongroups/service_group"),
        status=200,
        text="{}",
    )
    aioclient_mock.delete(
        ENDPOINT_URL.format("persongroups/service_group"),
        status=200,
        text="{}",
    )

    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    create_group(hass, "Service Group")
    await hass.async_block_till_done()

    entity = hass.states.get("microsoft_face.service_group")
    expect(entity).not_.to_be_none()
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    delete_group(hass, "Service Group")
    await hass.async_block_till_done()

    entity = hass.states.get("microsoft_face.service_group")
    expect(entity).to_be_none()
    expect(len(aioclient_mock.mock_calls)).to_equal(2)


@test
async def test_service_person(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test person services."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups"),
        text=await async_load_fixture(hass, "persongroups.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group2/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )

    with assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(3)

    aioclient_mock.post(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "create_person.json", DOMAIN),
    )
    aioclient_mock.delete(
        ENDPOINT_URL.format(
            "persongroups/test_group1/persons/25985303-c537-4467-b41d-bdb45cd95ca1"
        ),
        status=200,
        text="{}",
    )

    create_person(hass, "test group1", "Hans")
    await hass.async_block_till_done()

    entity_group1 = hass.states.get("microsoft_face.test_group1")

    expect(len(aioclient_mock.mock_calls)).to_equal(4)
    expect(entity_group1).not_.to_be_none().fatal()
    expect(entity_group1.attributes["Hans"]).to_equal(
        "25985303-c537-4467-b41d-bdb45cd95ca1"
    )

    delete_person(hass, "test group1", "Hans")
    await hass.async_block_till_done()

    entity_group1 = hass.states.get("microsoft_face.test_group1")

    expect(len(aioclient_mock.mock_calls)).to_equal(5)
    expect(entity_group1).not_.to_be_none().fatal()
    expect("Hans" in entity_group1.attributes).to_be_falsy()


@test
async def test_service_train(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test train groups services."""
    await async_setup_component(hass, "homeassistant", {})
    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    aioclient_mock.post(
        ENDPOINT_URL.format("persongroups/service_group/train"),
        status=200,
        text="{}",
    )

    train_group(hass, "Service Group")
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def test_service_face(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test person face services."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups"),
        text=await async_load_fixture(hass, "persongroups.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group2/persons"),
        text=await async_load_fixture(hass, "persons.json", DOMAIN),
    )

    config = {**CONFIG, "camera": {"platform": "demo"}}
    with assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, config)
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(3)

    aioclient_mock.post(
        ENDPOINT_URL.format(
            "persongroups/test_group2/persons/"
            "2ae4935b-9659-44c3-977f-61fac20d0538/persistedFaces"
        ),
        status=200,
        text="{}",
    )

    with patch(
        "homeassistant.components.camera.async_get_image",
        return_value=camera.Image("image/jpeg", b"Test"),
    ):
        face_person(hass, "test_group2", "David", "camera.demo_camera")
        await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(4)
    expect(aioclient_mock.mock_calls[3][2]).to_equal(b"Test")


@test
async def test_service_status_400(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test groups services with error."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.put(
        ENDPOINT_URL.format("persongroups/service_group"),
        status=400,
        text="{'error': {'message': 'Error'}}",
    )

    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    create_group(hass, "Service Group")
    await hass.async_block_till_done()

    entity = hass.states.get("microsoft_face.service_group")
    expect(entity).to_be_none()
    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test
async def test_service_status_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up component, test groups services with timeout."""
    await async_setup_component(hass, "homeassistant", {})
    aioclient_mock.put(
        ENDPOINT_URL.format("persongroups/service_group"),
        status=400,
        exc=TimeoutError(),
    )

    with _patch_update_store(), assert_setup_component(3, mf.DOMAIN):
        await async_setup_component(hass, mf.DOMAIN, CONFIG)

    create_group(hass, "Service Group")
    await hass.async_block_till_done()

    entity = hass.states.get("microsoft_face.service_group")
    expect(entity).to_be_none()
    expect(len(aioclient_mock.mock_calls)).to_equal(1)
