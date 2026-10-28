from backend.config import settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

class Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

mongo = Mongo()

async def connect():
    mongo.client = AsyncIOMotorClient(settings.mongo_uri, maxPoolSize=20,
                                      minPoolSize=1, serverSelectionTimeoutMS=5000)
    await mongo.client.admin.command("ping")  # fail fast
    mongo.db = mongo.client[settings.mongodb_db]
    await create_indexes(mongo.db)

async def create_indexes(db):
    await db.garments.create_index([("target_audience", 1), ("apparel_type", 1), ("category", 1)])
    await db.garments.create_index("slot")
    await db.tryon_sessions.create_index([("user_id", 1), ("created_at", -1)])
    await db.users.create_index("firebase_uid", unique=True)

async def disconnect():
    if mongo.client:
        mongo.client.close()

def get_db() -> AsyncIOMotorDatabase:
    return mongo.db
