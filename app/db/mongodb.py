import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bidding_info_new")

if MONGO_USER and MONGO_PASS:
    user = quote_plus(MONGO_USER)
    pwd = quote_plus(MONGO_PASS)  # 关键：会把 ## 变成 %23%23
    MONGO_DB_URL = (
        f"mongodb://{user}:{pwd}@{MONGO_HOST}:{MONGO_PORT}/"
        f"bidding_info_new?authSource=admin"
    )
else:
    MONGO_DB_URL = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

client = AsyncIOMotorClient(MONGO_DB_URL)
db = client[MONGO_DB_NAME]

async def get_database():
    return client.get_database(MONGO_DB_NAME)