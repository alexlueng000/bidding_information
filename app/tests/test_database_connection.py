# test the database connection
import asyncio

from app.db.mongodb import get_database

async def test_database_connection():
    db = await get_database()
    print(db)

async def test_connection():
    db = await get_database()
    try:
        await db.command('ping')
        print("Successfully connected to the database")
    except Exception as e:
        print(f"Error connecting to the database: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())

