import asyncio
import pytest
from backend.services import vto_engine as eng

def test_multi_piece_chains_outputs(monkeypatch):
    calls = []
    async def fake(person, garment, cat, desc=""):
        calls.append((person, cat)); return f"out{len(calls)}"
    monkeypatch.setattr(eng, "run_tryon", fake)
    comps = [{"name": "Blouse", "slot": "UPPER_BODY", "image_url": "b"},
             {"name": "Skirt", "slot": "LOWER_BODY", "image_url": "s"},
             {"name": "Dupatta", "slot": "ACCESSORY_OVERLAY", "image_url": "d"}]
    assert asyncio.run(eng.run_multi("p0", comps)) == "out3"
    assert calls == [("p0", "upper_body"), ("out1", "lower_body"), ("out2", "upper_body")]

def test_unconfigured_endpoint_raises(monkeypatch):
    monkeypatch.setattr(eng.settings, "hf_endpoint_url", "")
    with pytest.raises(RuntimeError):
        asyncio.run(eng.run_tryon("a", "b", "dresses"))
