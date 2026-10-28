import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from backend.security import verify_image
from backend.schemas import LiveFrame
from database.models import GarmentModel

def test_rejects_fake_image():
    with pytest.raises(HTTPException) as e: verify_image(b"MZ\x90 exe")
    assert e.value.status_code == 415

def test_rejects_oversize():
    with pytest.raises(HTTPException) as e: verify_image(b"\xff\xd8\xff" + b"0" * (10 * 1024 * 1024))
    assert e.value.status_code == 413

def test_accepts_jpeg():
    verify_image(b"\xff\xd8\xff\xe0" + b"0" * 100)

def test_garment_max_three_components():
    c = {"name": "x", "slot": "UPPER_BODY", "image_url": "u"}
    with pytest.raises(ValidationError):
        GarmentModel(name="s", apparel_type="ethnic", category="lehenga", components=[c] * 4)

def test_sheer_opacity_bounds():
    with pytest.raises(ValidationError):
        GarmentModel(name="s", apparel_type="ethnic", category="x",
                     components=[{"name": "d", "slot": "ACCESSORY_OVERLAY", "image_url": "u", "opacity": 0.1}])

def test_live_frame_needs_33_points():
    with pytest.raises(ValidationError): LiveFrame(keypoints=[{"x": 0, "y": 0}] * 10)
