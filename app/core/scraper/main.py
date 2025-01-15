import datetime
import asyncio

import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# from pydantic import BaseModel

from app.db.models.info import BiddingInfo
from app.db.mongodb import get_database
from app.core.scraper.classify import classify_info


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
    

# 检查日期是否在2024-11-30之后
def check_date(date_str: str) -> bool:
    # if the date is after 2024-11-30, return True
    # else return False
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    if date > datetime.datetime(2024, 11, 30):
        return True
    else:
        return False

# 从li标签中提取发布日期
def extract_date_from_li_item(li_item: BeautifulSoup) -> str:
    publish_date = li_item.find('span', class_='news-time').text.strip()
    return publish_date


def extract_info_from_li_item(li_item: BeautifulSoup) -> BiddingInfo:
    try:
        link = li_item.find('a', class_='text-overflow')
        href = link.get('href', '') if link else ''
        title = link.text.strip() if link else ''
        publish_date = li_item.find('span', class_='news-time').text.strip()
    except Exception as e:
        print(f"Error extracting info from li item: {e}")
        return None
    
    # print(f"Title: {title}")
    # print(f"URL: {href}")
    # print(f"Date: {publish_date}")

    # store the info to the database
    bidding_info = BiddingInfo(title=title, url=href, publish_date=publish_date)

    return bidding_info


# 获取最新的招标信息
# 直到获取到与数据库中最新招标信息相同的信息为止
async def get_shenzhen_bidding_info():
    print("Getting the latest bidding info at {}...".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
                info = extract_info_from_li_item(li_item)
                if await exist_info(info.publish_date, info.title, info.url):
                    return
                else:
                    await insert_info_to_db(info)
                    await classify_info(info)

                # print("--------------------------------")


        count += 1
        await asyncio.sleep(2)


# 数据库中最新的招标信息
async def get_the_latest_bidding_info() -> BiddingInfo:
    db = await get_database()
    cursor = db.bidding_info.find().sort("publish_date", -1).limit(1)
    results = await cursor.to_list(length=1)
    if results:
        print(f"The latest bidding info is: {results[0]}")
        return BiddingInfo(**results[0])
    else:
        return None

# 比较最新的招标信息与当前的招标信息
async def exist_info(publish_date: str, title: str, url: str) -> bool:

    db = await get_database()

    query = {
        "publish_date": publish_date,
        "title": title,
        "url": url
    }

    result = await db.bidding_info.find_one(query)

    return result is not None


# 插入新的招标信息到数据库
async def insert_info_to_db(info: BiddingInfo):
    info.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = await get_database()
    await db.bidding_infomation.insert_one(info.model_dump())

# 获取数据库中所有的招标信息
async def get_all_info_from_db():
    db = await get_database()
    cursor = db.bidding_infomation.find()
    results = await cursor.to_list(length=None)
    return [BiddingInfo(**result) for result in results]


# don't use this function anymore
async def reorgaize_the_info_from_db():
    history_info = await get_all_info_from_db()
    history_info = list(reversed(history_info))
    
    count = 1
    latest_info_count = 0
    latest_info = await get_the_latest_bidding_info()

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
                info = extract_info_from_li_item(li_item)
                if exist_info(latest_info, info.publish_date, info.title, info.url):
                    break  # 跳出 for 循环
                else:
                    history_info.append(info)
                    latest_info_count += 1
                    print(f"The latest info count is: {latest_info_count}")
            else:
                # 如果 for 循环没有 break，继续爬取下一页
                count += 1
                await asyncio.sleep(2)
                continue  # 继续 while 循环
            
            # 如果 for 循环中 break 了，跳出 while 循环
            break
    
    for info in history_info:
        info.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await insert_info_to_db(info)
    

async def main():
    scheduler = AsyncIOScheduler()

    # 使用 CronTrigger 添加定时任务
    scheduler.add_job(
        get_shenzhen_bidding_info,
        trigger=CronTrigger(hour=8),  # 每天 8 点执行
    )
    scheduler.add_job(
        get_shenzhen_bidding_info,
        trigger=CronTrigger(hour=12),  # 每天 12 点执行
    )
    scheduler.add_job(
        get_shenzhen_bidding_info,
        trigger=CronTrigger(hour=16),  # 每天 16 点执行
    )
    scheduler.add_job(
        get_shenzhen_bidding_info,
        trigger=CronTrigger(hour=20),  # 每天 20 点执行
    )

    scheduler.start()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        print("Stopping the scheduler...")


if __name__ == "__main__":
    asyncio.run(main())
