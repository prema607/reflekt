"""Run: python -m backend.worker"""
import asyncio, json
from backend.config import settings
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import redis.asyncio as aioredis
from database import database as dbm
from backend.services.vto_engine import run_multi

QUEUE = "tryon"

async def process(job: dict):
    db, sid = dbm.get_db(), ObjectId(job["job_id"])
    upd = lambda **f: db.tryon_sessions.update_one(
        {"_id": sid}, {"$set": {**f, "updated_at": datetime.now(timezone.utc)}})
    await upd(status="PROCESSING")
    try:
        comps = []
        for gid in job["garment_ids"]:
            g = await db.garments.find_one({"_id": ObjectId(gid)})
            comps += g["components"]
        await upd(status="COMPLETED", result_url=await run_multi(job["person_image_url"], comps))
    except Exception as e:
        await upd(status="FAILED", error=str(e)[:500])

async def sweep():
    """Fail jobs stuck in PROCESSING/PENDING for >10 minutes (crashed worker)."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    await dbm.get_db().tryon_sessions.update_many(
        {"status": {"$in": ["PROCESSING", "PENDING"]}, "updated_at": {"$lt": cutoff}},
        {"$set": {"status": "FAILED", "error": "Timed out"}})

async def main():
    await dbm.connect()
    r = aioredis.from_url(settings.redis_url)
    last = 0.0
    while True:
        if asyncio.get_event_loop().time() - last > 60:
            await sweep(); last = asyncio.get_event_loop().time()
        item = await r.blpop(QUEUE, timeout=5)
        if item:
            await process(json.loads(item[1]))

if __name__ == "__main__":
    asyncio.run(main())
