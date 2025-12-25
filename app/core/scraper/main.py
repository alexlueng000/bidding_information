import os
import datetime
import asyncio
import json
from typing import Optional

import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


from app.db.models.info import BiddingInfo
from app.db.mongodb import get_database
from app.core.scraper.scrape_full_info import scrape_full_infomation

from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai_url = 'https://openkey.cloud/v1'


client = OpenAI(api_key=api_key, base_url="https://openkey.cloud/v1")

# 从深圳政府采购网获取招标信息
base_url = "http://zfcg.szggzy.com:8081"
first_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/list.html"
next_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/{}.html"


proxy_pool = [
    "http://118.178.197.213:3128",
    "http://39.101.161.223:8090",
    "http://118.25.110.238:443",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/list.html",
}

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
    

# 检查日期是否在2024-10-31之后
def check_date(date_str: str) -> bool:
    # if the date is after 2024-10-31, return True
    # else return False
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    if date > datetime.datetime(2024, 10, 31):
        return True
    else:
        return False

# 从li标签中提取发布日期
def extract_date_from_li_item(li_item: BeautifulSoup) -> str:
    publish_date = li_item.find('span', class_='news-time').text.strip()
    return publish_date



def extract_info_from_li_item(li_item: BeautifulSoup) -> Optional[BiddingInfo]:
    try:
        link = li_item.find('a', class_='text-overflow')
        if not link:
            raise ValueError("未找到链接节点 <a class='text-overflow'>")

        href = link.get('href', '').strip()
        title = link.get_text(strip=True)

        span = li_item.find('span', class_='news-time')
        publish_date = span.get_text(strip=True) if span else ''

        return BiddingInfo(title=title, url=href, publish_date=publish_date)

    except Exception as e:
        preview = li_item.text.strip().replace("\n", "")[:50]
        print(f"[extract_info] ❌ 解析失败: {e} | 内容预览: {preview}")
        return None

# 分类信息: 如果信息中包含南方科技大学、深圳大学、深圳技术大学、深圳国际量子研究院、深圳综合粒子设施研究院，则将信息分类到相应的大学
async def classify_info(info: BiddingInfo):

    db = await get_database()
    
    info.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")



# 获取最新的招标信息
# 直到获取到与数据库中最新招标信息相同的信息为止
async def get_shenzhen_bidding_info():

    # db = await get_database()

    print("Getting the latest bidding info at {}...".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    count = 1
    
    while True:

        print("现在爬取第{count}页", count)
        if count == 1:
            url = first_page_url
        else:
            url = next_page_url.format(count)

        session = requests.Session()
        session.headers.update(headers)
        session.get(first_page_url, timeout=20)

        response = session.get(url)
        
        soup = BeautifulSoup(response.text, "html.parser")

        news_items = soup.find('ul', {'class': 'news-items', 'id': 'infoContent'})

        if news_items:
            li_items = news_items.find_all('li')

            for li_item in li_items:
                print(f"标题：{li_item.text}")
                info = extract_info_from_li_item(li_item)
                if info:
                    await insert_info_to_db(info, session)
                else:
                    continue
                # print("--------------------------------")
        count += 1
        await asyncio.sleep(60)  


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


# 获取数据库中所有的招标信息
async def get_all_info_from_db():
    db = await get_database()
    cursor = db.bidding_infomation.find()
    results = await cursor.to_list(length=None)
    return [BiddingInfo(**result) for result in results]



# 插入新的招标信息到数据库
async def insert_info_to_db(info: BiddingInfo, session: requests.Session) -> bool:

    # 在插入之前，先判断数据库中是否已经存在了该项目信息
    db = await get_database()

    query = {
        "publish_date": info.publish_date,
        "title": info.title,
        "url": info.url
    }

    exist_info = await db.bidding_infomation.find_one(query)

    # 如果已经存在了，就不插入数据库了
    if exist_info:
        return False

    info.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 插入主表
    await db.bidding_infomation.insert_one(info.model_dump())

    # 获取完整的招标信息
    full_url = base_url + info.url

    # 获取详情页数据
    data = scrape_full_infomation(full_url, session=session, referer=first_page_url)

    # 判断是否成功获取数据
    if not data:
        print(f"[insert_info_to_db] ⚠️ 未获取到详情页数据，跳过该记录: {full_url}")
        return False
    
    # 如果是重点高校，则插入对应的表
    for keyword in [
        "南方科技大学",
        "深圳大学",
        "深圳技术大学",
        "深圳国际量子研究院",
        "深圳先进光源研究院",
        "北京大学深圳研究生院",
        "清华大学深圳国际研究生院",
        "深圳信息职业技术学院",
        "深圳湾实验室",
        "深圳北理莫斯科大学",
        "北京理工大学深圳汽车研究院",
        "深圳医学科学院",
        "哈尔滨工业大学（深圳）",
        "香港中文大学（深圳）",
        "深圳理工大学",
        "深圳职业技术大学",
        "鹏城实验室",
        "中山大学深圳校区"
    ]:
        if keyword in info.title or keyword in data['采购单位']:
            # 判断该项目是否属于货物类项目
            completion = client.chat.completions.create(
                model="gpt-5-2025-08-07",
                stream=False,
                messages=[
                    {"role": "system", "content": "你是一位招标采购专家，请根据我提供的招标项目描述信息，判断这个项目是否属于货物类项目。"},
                    {"role": "user", "content": f"以下是项目描述：\n"
                                    f"项目名称：{data['项目名称']}\n"
                                    f"采购品目：{data['采购品目']}\n"
                                    f"采购需求概况：{data['采购需求概况']}\n"
                                    "请用JSON格式回复'true'或者'false':{is_good: ...}"}
                ],
                response_format={"type": "json_object"}
            )
        
            try:
                response_data = json.loads(completion.choices[0].message.content)
                is_good = response_data.get("is_good", False)
            except json.JSONDecodeError:
                print(f"无法解析返回内容: {completion.choices[0].message.content}")
                is_good = False

            info.is_good = is_good

            match keyword:
                case "南方科技大学":
                    if '南方科技大学医院' != data['采购单位']:
                        db.nkd.insert_one(info.model_dump())
                case "深圳大学":
                    if '总医院' not in info.title and '附属中学' not in info.title and '附属华南医院' not in info.title:
                        db.szu.insert_one(info.model_dump())
                case "深圳技术大学":
                    db.sztu.insert_one(info.model_dump())
                case "深圳国际量子研究院":
                    db.siqse.insert_one(info.model_dump())
                case "深圳先进光源研究院":
                    db.iasf.insert_one(info.model_dump())
                case "北京大学深圳研究生院":
                    db.pkusz.insert_one(info.model_dump())
                case "清华大学深圳国际研究生院":
                    db.tsinghua.insert_one(info.model_dump())
                case "深圳信息职业技术学院":
                    db.sziit.insert_one(info.model_dump())
                case "深圳湾实验室":
                    db.szbl.insert_one(info.model_dump())
                case "深圳北理莫斯科大学":
                    db.smbu.insert_one(info.model_dump())
                case "北京理工大学深圳汽车研究院":
                    db.szari.insert_one(info.model_dump())
                case "深圳医学科学院":
                    db.szyxkxy.insert_one(info.model_dump())
                case "哈尔滨工业大学（深圳）":
                    db.hgd.insert_one(info.model_dump())
                case "香港中文大学（深圳）":
                    db.hkc.insert_one(info.model_dump())
                case "深圳理工大学":
                    db.szlg.insert_one(info.model_dump())
                case "深圳职业技术大学":
                    db.szzyjs.insert_one(info.model_dump())
                case "鹏城实验室":
                    db.pcsys.insert_one(info.model_dump())
                case "中山大学深圳校区":
                    db.szust.insert_one(info.model_dump())
    return True

async def main():
    # await get_shenzhen_bidding_info()
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
    # asyncio.run(main())
    asyncio.run(get_shenzhen_bidding_info())