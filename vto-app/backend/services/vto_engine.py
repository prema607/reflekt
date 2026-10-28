"""Client for the Hugging Face Inference Endpoint defined in hf_endpoint/handler.py."""
import asyncio, base64
import cloudinary.uploader, httpx
from backend.config import settings

SLOT_TO_CATEGORY = {"UPPER_BODY": "upper_body", "LOWER_BODY": "lower_body",
                    "FULL_BODY": "dresses", "ACCESSORY_OVERLAY": "upper_body"}

async def _fetch_b64(url: str, c: httpx.AsyncClient) -> str:
    r = await c.get(url); r.raise_for_status()
    return base64.b64encode(r.content).decode()

async def run_tryon(person_url: str, garment_url: str, category: str, description: str = "") -> str:
    """One diffusion pass. Returns the Cloudinary URL of the rendered image."""
    if not settings.hf_endpoint_url or not settings.huggingface_api_token:
        raise RuntimeError("HF_ENDPOINT_URL / HUGGINGFACE_API_TOKEN not configured")
    headers = {"Authorization": f"Bearer {settings.huggingface_api_token}"}
    async with httpx.AsyncClient(timeout=300) as c:
        payload = {"inputs": {"person_image": await _fetch_b64(person_url, c),
                              "garment_image": await _fetch_b64(garment_url, c),
                              "category": category, "description": description}}
        for attempt in range(6):  # endpoint may be scaled to zero (503 while warming)
            r = await c.post(settings.hf_endpoint_url, json=payload, headers=headers)
            if r.status_code in (502, 503):
                await asyncio.sleep(20 * (attempt + 1)); continue
            r.raise_for_status(); break
        else:
            raise RuntimeError("HF endpoint unavailable")
    img = base64.b64decode(r.json()["image"])
    up = await asyncio.to_thread(cloudinary.uploader.upload, img, folder="vto/results")
    return up["secure_url"]

async def run_multi(person_url: str, components: list[dict]) -> str:
    """Multi-piece sets (Lehenga = blouse + skirt + dupatta): one pass per piece."""
    current = person_url
    for c in components:
        current = await run_tryon(current, c["image_url"], SLOT_TO_CATEGORY[c["slot"]], c["name"])
    return current
