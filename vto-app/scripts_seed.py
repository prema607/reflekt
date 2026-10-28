"""python scripts_seed.py  -> inserts sample garments (replace image URLs with yours)."""
import asyncio
from database import database as dbm
S = [
 {"name":"Red Banarasi Saree","target_audience":"women","apparel_type":"ethnic","category":"saree",
  "components":[{"name":"Saree","slot":"FULL_BODY","image_url":"https://example.com/saree.jpg","opacity":1.0}]},
 {"name":"Organza Dupatta Kurti","target_audience":"women","apparel_type":"ethnic","category":"kurti",
  "components":[{"name":"Kurti","slot":"UPPER_BODY","image_url":"https://example.com/kurti.jpg","opacity":1.0},
                {"name":"Dupatta","slot":"ACCESSORY_OVERLAY","image_url":"https://example.com/dup.jpg","opacity":0.5}]},
]
async def main():
    await dbm.connect(); await dbm.get_db().garments.insert_many(S); print("seeded")
asyncio.run(main())
