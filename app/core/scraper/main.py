import datetime

import requests
from bs4 import BeautifulSoup

# from pydantic import BaseModel

from app.db.models.info import BiddingInfo
from app.db.mongodb import get_database


# 从深圳政府采购网获取招标信息
base_url = "http://zfcg.szggzy.com:8081"
first_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/list.html"
next_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/{}.html"

## steps
## 1. 获取页面内容
## 2. 解析页面内容
## 3. 提取当天的招标信息
## 4. 如果有第2页，则获取第2页的页面内容，直到没有当天的信息为止
## 5. 存储到数据库

def compare_publish_time(time_str: str) -> bool:
    # 2025-01-12 
    # if is not today's news, return False
    # if is today's news, return True
    # else return False

    today = datetime.now().strftime("%Y-%m-%d")
    if time_str != today:
        return False
    else:
        return True

async def extract_info_from_li_item(li_item: BeautifulSoup):
    try:
        link = li_item.find('a', class_='text-overflow')
        href = link.get('href', '') if link else ''
        title = link.text.strip() if link else ''
        publish_date = li_item.find('span', class_='news-time').text.strip()
    except Exception as e:
        print(f"Error extracting info from li item: {e}")
        return None
    
    print(f"Title: {title}")
    print(f"URL: {href}")
    print(f"Date: {publish_date}")

    # store the info to the database
    bidding_info = BiddingInfo(title=title, url=href, publish_date=publish_date)

    db = await get_database()
    # I want to check if the table exists, if not, create it
    collections = await db.list_collection_names()
    print(collections)

    if "info" not in collections:
        await db.create_collection("info")
        print("Collection created")
    
    await db.bidding_info.insert_one(bidding_info.model_dump())
    print("Info stored")


async def get_shenzhen_bidding_info():

    response = requests.get(first_page_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # 获取当前页面的招标信息
    # bid_info_divs = soup.find_all('div', class_='bid-info')
    # for bid_info_div in bid_info_divs:

    news_items = soup.find('ul', {'class': 'news-items', 'id': 'infoContent'})
    if news_items:
        li_items = news_items.find_all('li')

        for li_item in li_items:
            await extract_info_from_li_item(li_item)
            print("--------------------------------")
    

    # print(bid_info_divs)


if __name__ == "__main__":

    import asyncio
    asyncio.run(get_shenzhen_bidding_info())
