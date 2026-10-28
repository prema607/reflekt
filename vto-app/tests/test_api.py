from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)  # no `with`: lifespan (DB/Redis) is not started

def test_snapshot_rejects_non_image():
    r = client.post("/api/v1/try-on/snapshot", files={"image": ("a.jpg", b"not an image")},
                    data={"garment_ids": "[]"})
    assert r.status_code == 415

def test_status_bad_id():
    assert client.get("/api/v1/try-on/status/not-an-id").status_code == 400

def test_cors_blocks_unknown_origin():
    r = client.options("/api/v1/garments", headers={"Origin": "http://evil.example",
                       "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers
