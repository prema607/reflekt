import io
from PIL import Image
from backend.config import Settings

def test_settings_defaults_and_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://x"); monkeypatch.setenv("AUTH_REQUIRED", "true")
    s = Settings()
    assert s.mongo_uri == "mongodb://x" and s.auth_required is True

def test_normalize_person_size_and_lowlight():
    from backend.services.preprocessor import normalize_person
    buf = io.BytesIO(); Image.new("RGB", (1000, 1000), (10, 10, 10)).save(buf, "JPEG")
    out = Image.open(io.BytesIO(normalize_person(buf.getvalue())))
    assert out.size == (768, 1024)
