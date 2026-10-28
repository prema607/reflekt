import json
from backend.config import settings
from contextlib import asynccontextmanager
from bson import ObjectId
import cloudinary.uploader
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from database import database as dbm
from database.models import TryOnSessionModel
from backend.schemas import LiveFrame, SnapshotResponse, StatusResponse
from backend.worker import QUEUE
from backend.security import verify_image
from backend.auth import current_uid, admin_uid
from database.models import GarmentModel
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('vto')
from backend.services.preprocessor import normalize_person, clean_garment

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbm.connect()
    app.state.redis = aioredis.from_url(settings.redis_url)
    yield
    await dbm.disconnect()
    await app.state.redis.close()

app = FastAPI(title="Women's Dual-Mode VTO", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware,
    allow_origins=[o for o in settings.allowed_origins.split(",") if o],
    allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

@app.get("/api/v1/health")
async def health():
    await dbm.mongo.client.admin.command("ping")
    return {"status": "ok"}

@app.get("/api/v1/garments")
async def garments(target_audience: str = "women", apparel_type: str | None = None,
                   category: str | None = None, limit: int = 50, skip: int = 0):
    q = {"target_audience": target_audience}
    if apparel_type: q["apparel_type"] = apparel_type
    if category: q["category"] = category
    docs = await dbm.get_db().garments.find(q).skip(skip).limit(min(limit, 100)).to_list(None)
    for d in docs: d["_id"] = str(d["_id"])
    return docs

@app.post("/api/v1/try-on/snapshot", status_code=202, response_model=SnapshotResponse)
@limiter.limit("5/minute")
async def snapshot(request: Request, image: UploadFile = File(...), garment_ids: str = Form(...),
                   uid: str = Depends(current_uid)):
    data = await image.read()
    verify_image(data)
    data = normalize_person(data)
    try:
        ids = json.loads(garment_ids)
        assert isinstance(ids, list) and all(ObjectId.is_valid(i) for i in ids)
    except Exception:
        raise HTTPException(422, 'Invalid garment_ids')
    if not 1 <= len(ids) <= 3:
        raise HTTPException(422, "1-3 garment ids required")
    up = cloudinary.uploader.upload(data, folder="vto/person")
    sess = TryOnSessionModel(user_id=uid, garment_ids=ids, person_image_url=up["secure_url"])
    res = await dbm.get_db().tryon_sessions.insert_one(sess.model_dump(exclude={"id"}))
    jid = str(res.inserted_id)
    await app.state.redis.rpush(QUEUE, json.dumps(
        {"job_id": jid, "garment_ids": ids, "person_image_url": up["secure_url"]}))
    return SnapshotResponse(job_id=jid)

@app.get("/api/v1/try-on/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    if not ObjectId.is_valid(job_id): raise HTTPException(400, "Bad job id")
    s = await dbm.get_db().tryon_sessions.find_one({"_id": ObjectId(job_id)})
    if not s: raise HTTPException(404, "Job not found")
    return StatusResponse(job_id=job_id, status=s["status"],
                          result_url=s.get("result_url"), error=s.get("error"))

@app.websocket("/ws/live-tryon")
async def live(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            frame = LiveFrame.model_validate_json(await ws.receive_text())
            ls = frame.keypoints[11]  # MediaPipe left shoulder = saree pallu anchor
            await ws.send_json({"pallu_anchor": {"x": ls.x, "y": ls.y}})
    except WebSocketDisconnect:
        pass

@app.post("/api/v1/admin/garments", status_code=201)
async def add_garment(name: str = Form(...), category: str = Form(...),
                      apparel_type: str = Form("ethnic"), slot: str = Form("FULL_BODY"),
                      opacity: float = Form(1.0), image: UploadFile = File(...),
                      _: str = Depends(admin_uid)):
    data = await image.read()
    verify_image(data)
    up = cloudinary.uploader.upload(clean_garment(data), folder="vto/garments")
    g = GarmentModel(name=name, apparel_type=apparel_type, category=category,
                     components=[{"name": name, "slot": slot, "image_url": up["secure_url"], "opacity": opacity}])
    res = await dbm.get_db().garments.insert_one(g.model_dump(exclude={"id"}))
    log.info("garment added %s", res.inserted_id)
    return {"id": str(res.inserted_id), "image_url": up["secure_url"]}
