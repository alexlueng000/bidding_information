"""
Test MongoDB connection and data retrieval.
Run with: python -m app.tests.test_mongo_connection
"""
import asyncio
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


async def test_mongodb_connection():
    print("=" * 50)
    print("Testing MongoDB Connection")
    print("=" * 50)

    # Build connection string
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASS = os.getenv("MONGO_PASS")
    MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
    MONGO_PORT = os.getenv("MONGO_PORT", "27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bidding_info_new")

    print("MONGO_USER repr:", repr(os.getenv("MONGO_USER")))
    print("MONGO_PASS repr:", repr(os.getenv("MONGO_PASS")))
    print("MONGO_HOST repr:", repr(os.getenv("MONGO_HOST")))
    print("MONGO_DB_NAME repr:", repr(os.getenv("MONGO_DB_NAME")))

    if MONGO_USER and MONGO_PASS:
        user = quote_plus(MONGO_USER)
        pwd = quote_plus(MONGO_PASS)
        mongo_url = f"mongodb://{user}:{pwd}@{MONGO_HOST}:{MONGO_PORT}/?authSource=bidding_info_new"
        print(f"Connection Mode: Authenticated")
        print(f"Host: {MONGO_HOST}:{MONGO_PORT}")
        print(f"User: {MONGO_USER}")
    else:
        mongo_url = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"
        print(f"Connection Mode: No Auth")
        print(f"Host: {MONGO_HOST}:{MONGO_PORT}")

    print(f"Database: {MONGO_DB_NAME}")
    print("-" * 50)

    try:
        # Test connection
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)

        # Force connection
        await client.admin.command('ping')
        print("✓ MongoDB server connection: SUCCESS")

        # Get database
        db = client[MONGO_DB_NAME]
        print(f"✓ Database '{MONGO_DB_NAME}' accessed")

        # List all collections
        collections = await db.list_collection_names()
        print(f"✓ Found {len(collections)} collections:")
        for col in collections:
            print(f"  - {col}")

        # Test bidding_infomation collection
        if "bidding_infomation" in collections:
            count = await db.bidding_infomation.count_documents({})
            print(f"\n✓ 'bidding_infomation' collection has {count} documents")

            if count > 0:
                # Get one sample document
                sample = await db.bidding_infomation.find_one({})
                print(f"\nSample document:")
                print(f"  - Title: {sample.get('title', 'N/A')}")
                print(f"  - Publish Date: {sample.get('publish_date', 'N/A')}")
                print(f"  - URL: {sample.get('url', 'N/A')}")
                print(f"  - Is Good: {sample.get('is_good', 'N/A')}")
                print(f"  - Organization: {sample.get('organization', 'N/A')}")
            else:
                print("\n⚠ Collection is empty. Run the scraper to populate data.")
        else:
            print("\n⚠ 'bidding_infomation' collection not found.")

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)

        client.close()
        return True

    except Exception as e:
        print(f"\n✗ Connection FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Check if MongoDB is running:")
        print("   - Windows: Check services for 'MongoDB'")
        print("2. Verify credentials in .env file")
        print("3. Check if auth is enabled in MongoDB")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_mongodb_connection())
    exit(0 if result else 1)
