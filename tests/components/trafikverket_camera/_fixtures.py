"""Tryke fixtures for the trafikverket_camera integration."""

from datetime import datetime

from pytrafikverket import CameraInfoModel
from tryke import fixture

from homeassistant.util import dt as dt_util


@fixture
def get_camera() -> CameraInfoModel:
    """Construct Camera Mock."""
    return CameraInfoModel(
        camera_name="Test Camera",
        camera_id="1234",
        active=True,
        deleted=False,
        description="Test Camera for testing",
        direction="180",
        fullsizephoto=True,
        location="Test location",
        modified=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        phototime=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        photourl="https://www.testurl.com/test_photo.jpg",
        status="Running",
        camera_type="Road",
    )


@fixture
def get_camera2() -> CameraInfoModel:
    """Construct Camera Mock 2."""
    return CameraInfoModel(
        camera_name="Test Camera2",
        camera_id="5678",
        active=True,
        deleted=False,
        description="Test Camera for testing2",
        direction="180",
        fullsizephoto=True,
        location="Test location2",
        modified=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        phototime=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        photourl="https://www.testurl.com/test_photo2.jpg",
        status="Running",
        camera_type="Road",
    )


@fixture
def get_cameras() -> list[CameraInfoModel]:
    """Construct Camera Mock with multiple cameras."""
    return [
        CameraInfoModel(
            camera_name="Test Camera",
            camera_id="1234",
            active=True,
            deleted=False,
            description="Test Camera for testing",
            direction="180",
            fullsizephoto=True,
            location="Test location",
            modified=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
            phototime=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
            photourl="https://www.testurl.com/test_photo.jpg",
            status="Running",
            camera_type="Road",
        ),
        CameraInfoModel(
            camera_name="Test Camera2",
            camera_id="5678",
            active=True,
            deleted=False,
            description="Test Camera for testing2",
            direction="180",
            fullsizephoto=True,
            location="Test location2",
            modified=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
            phototime=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
            photourl="https://www.testurl.com/test_photo2.jpg",
            status="Running",
            camera_type="Road",
        ),
    ]


@fixture
def get_camera_no_location() -> CameraInfoModel:
    """Construct Camera Mock."""
    return CameraInfoModel(
        camera_name="Test Camera",
        camera_id="1234",
        active=True,
        deleted=False,
        description="Test Camera for testing",
        direction="180",
        fullsizephoto=True,
        location=None,
        modified=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        phototime=datetime(2022, 4, 4, 4, 4, 4, tzinfo=dt_util.UTC),
        photourl="https://www.testurl.com/test_photo.jpg",
        status="Running",
        camera_type="Road",
    )
