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
    

def check_date(date_str: str) -> bool:
    # if the date is after 2024-11-30, return True
    # else return False
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    if date > datetime.datetime(2024, 11, 30):
        return True
    else:
        return False
    
def extract_date_from_li_item(li_item: BeautifulSoup) -> str:
    publish_date = li_item.find('span', class_='news-time').text.strip()
    return publish_date


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
    
    await db.bidding_info.insert_one(bidding_info.model_dump())
    print("Info stored")



# need to scrape all the info after the 2024-11-30

async def get_shenzhen_bidding_info():

    count = 1

    while True:
        if count == 1:
            url = first_page_url
        else:
            url = next_page_url.format(count)

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        news_items = soup.find('ul', {'class': 'news-items', 'id': 'infoContent'})
        if news_items:
            li_items = news_items.find_all('li')

            for li_item in li_items:
                publish_date = extract_date_from_li_item(li_item)
                if check_date(publish_date):
                    await extract_info_from_li_item(li_item)
                    print("--------------------------------")
                else:
                    # if the date is not after 2024-11-30, end the loop and return
                    return

        count += 1
        await asyncio.sleep(2)
    

    # print(bid_info_divs)


if __name__ == "__main__":

    import asyncio
    asyncio.run(get_shenzhen_bidding_info())
