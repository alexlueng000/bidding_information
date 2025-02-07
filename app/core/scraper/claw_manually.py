import asyncio

# from .main import get_shenzhen_bidding_info
from app.core.scraper.main import get_shenzhen_bidding_info
from app.core.scraper.main import get_all_info_from_db

def classify_exist_info():
    all_info = get_all_info_from_db()

    for info in all_info:
        pass




async def main():
    await get_shenzhen_bidding_info()
    

if __name__ == "__main__":
    asyncio.run(main())

