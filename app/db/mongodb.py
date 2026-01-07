from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DB_URL = "mongodb://localhost:27017"
MONGO_DB_NAME = "bidding_info_new"

client = AsyncIOMotorClient(MONGO_DB_URL)
# print(client)
db = client[MONGO_DB_NAME]
# print(db)


async def get_database():
    return client.get_database(MONGO_DB_NAME)


