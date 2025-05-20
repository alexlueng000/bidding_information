import asyncio
import re
import json
import datetime
from typing import List
# from .main import get_shenzhen_bidding_info
from app.core.scraper.main import get_shenzhen_bidding_info
from app.core.scraper.main import get_all_info_from_db
from app.core.scraper.main import scrape_full_infomation
from app.core.scraper.main import extract_info_from_li_item
from app.core.scraper.main import check_date
# from app.core.scraper.main import insert_info_to_db
from app.core.scraper.scrape_full_info import scrape_full_infomation
from app.db.mongodb import get_database
from app.db.models.info import BiddingInfo


import requests
from bs4 import BeautifulSoup


from openai import OpenAI


api_key = 'sk-vUyp1vFsIO0OxaIi0c8573Ed7e5e4e18A58618378eE9D106'
openai_url = 'https://openkey.cloud/v1'

base_url = "http://zfcg.szggzy.com:8081"

first_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/list.html"
next_page_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/{}.html"
page_after_100_url = "http://zfcg.szggzy.com:8081/gsgg/002001/002001001/list.html?categoryNum=002001001&pageIndex={}"


client = OpenAI(api_key=api_key, base_url="https://openkey.cloud/v1")

szu_bidding_website = 'https://bidding.szu.edu.cn/cggg/cgyxgk.htm'
prefix = 'https://bidding.szu.edu.cn'

class SZUBiddingInfo:
    def __init__(self, date: str, titleColor: str, showTitle: str, tipsTitle: str, 
                 cssTitleColor: str, showDate: str, url: str):
        self.date = date
        self.titleColor = titleColor
        self.showTitle = showTitle
        self.tipsTitle = tipsTitle
        self.cssTitleColor = cssTitleColor
        self.showDate = showDate
        self.url = url

    def __repr__(self):
        return f"SZUBiddingInfo(date={self.date}, showTitle={self.showTitle}, tipsTitle={self.tipsTitle}, url={self.url})"

def classify_exist_info():
    all_info = get_all_info_from_db()

    for info in all_info:
        pass

def specific_info(url: str) -> str:
    print('具体URL: ', url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # # print(response.text)
    p_tags = soup.find_all('p')

    # url = ''

    for p_tag in p_tags:
        # print(p_tag)
        match_url = re.search(r'http[s]?://[^\s]+', p_tag.text)
        if match_url:
            result = match_url.group(0)
            # print(url)
            url = result
    print('找到源网址：', url)
    return url

async def claw_szu_only():

    db = await get_database()

    response = requests.get(szu_bidding_website)
    response.encoding = 'utf-8'
    # print(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', text=re.compile('var datanews ='))

    if script_tag:
        match = re.search(r'var datanews = (\[.*?\]);', script_tag.string)
        if match:
            datanews = match.group(1)
            info_list = parse_datanews(datanews)
            for info in info_list:
                # 去掉开头两个置顶项
                if "置顶" in info.showTitle:
                    continue
                target_url = prefix + info.url.lstrip('..')
                source_url = specific_info(target_url)
                data = scrape_full_infomation(source_url)

                if not data:
                    continue

                print('项目标题：', data['项目标题'])
                result = await db.bidding_infomation.find_one(data['项目标题'])
                # 根据标题来判断数据库里是否已经存在这个项目了
                if result:
                    print("项目已经存在")
                    continue

                # 判断该项目是否属于货物类项目
                completion = client.chat.completions.create(
                    model="gpt-4o-2024-08-06",
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

                address = ""

                if 'zfcg' in source_url:
                    address = source_url.replace("http://zfcg.szggzy.com:8081", "", 1)
                else:
                    address = source_url

                info = BiddingInfo(
                    title=data['项目标题'],
                    url=address,
                    publish_date=data['发布日期'],
                    is_good=is_good,
                    created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                print('项目信息：', info)
                await db.bidding_information.insert_one(info.model_dump())
                await db.szu.insert_one(info.model_dump())
                # specific_info(source_url)
                 
                await asyncio.sleep(5)
                
        else:
            print('没有找到datanews变量的数据')

def parse_datanews(datanews_str: str) -> List[SZUBiddingInfo]:
    # 解析 JSON 字符串
    datanews = json.loads(datanews_str)
    
    # 创建 BiddingInfo 实例列表
    bidding_info_list = []
    for item in datanews:
        # 提取每个 item 的信息并创建 BiddingInfo 实例
        bidding_info = SZUBiddingInfo(
            date=item["date"],
            titleColor=item["titleColor"],
            showTitle=item["showTitle"],
            tipsTitle=item["tipsTitle"],
            cssTitleColor=item["cssTitleColor"],
            showDate=item["showDate"],
            url=item["url"]["asString"]
        )
        bidding_info_list.append(bidding_info)
    
    return bidding_info_list

async def main():
    await get_shenzhen_bidding_info()


def crawl_test():
    # 实际URL：https://www.szggzy.com/cms/api/v1/trade/content/detail?contentId=2385842
    response = requests.get('https://www.szggzy.com/cms/api/v1/trade/content/detail?contentId=2385842')
    response.encoding = 'utf-8'
    # print(response.text)

    # 发布日期，项目标题，采购品目，项目名称，采购需求概况
    if response.status_code == 200:
        # result = json.dumps(response.json(), indent=4, ensure_ascii=False)
        # result = response.json()
        result = json.loads(response.text)
        data = {}
        data['发布日期'] = result['data']['releaseTime']
        data['项目标题'] = result['data']['title']
        data['采购品目'] = result['data']['nodeList']
        data['项目名称'] = result['data']['title']
        
        soup = BeautifulSoup(result['data']['txt'], 'html.parser')

        target_td = soup.find("td", text="预计项目概况：")
        if target_td:
            project_desc = target_td.find_next("td").get_text(strip=True)
            data['采购需求概况'] = project_desc 

        print(data)

async def find_one():
    db = await get_database()
    result = await db.bidding_infomation.find_one({'title': '深圳市市场监督管理局龙岗监管局农产品安全监管意向公开'})
    print('result: ', result)
    
# 北京大学深圳研究生院、清华大学深圳国际研究生院、深圳信息职业技术学院、深圳湾实验室、深圳北理莫斯科大学、北京理工大学深圳汽车研究院（电动车辆国家工程实验室深圳研究院）
# 北京大学深圳研究生院 pkusz
# 清华大学深圳国际研究生院 tsinghua
# 深圳信息职业技术学院 sziit
# 深圳湾实验室 szbl
# 深圳北理莫斯科大学 smbu
# 北京理工大学深圳汽车研究院 szari
async def classify_university():
    db = await get_database()
    results = await db.bidding_infomation.find({
        'title': {
            '$regex': '北京大学深圳研究生院|清华大学深圳国际研究生院|深圳信息职业技术学院|深圳湾实验室|深圳北理莫斯科大学|北京理工大学深圳汽车研究院',
            '$options': 'i'  # 不区分大小写
        }
    }).to_list(None)
    for result in results:
        # print('result: ', result)
        title = result.get('title')
        for keyword in [
            "北京大学深圳研究生院",
            "清华大学深圳国际研究生院",
            "深圳信息职业技术学院",
            "深圳湾实验室",
            "深圳北理莫斯科大学",
            "北京理工大学深圳汽车研究院"
        ]:
            if keyword in title:
                suffix_url = result.get('url')
                full_url = base_url + suffix_url
                # print(result['title'] + ": " + full_url)
                data = scrape_full_infomation(full_url)

                # 判断该项目是否属于货物类项目
                completion = client.chat.completions.create(
                    model="gpt-4o-2024-08-06",
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

                result['is_good'] = is_good

                match keyword:
                    case "北京大学深圳研究生院":
                        # info.university = "南方科技大学"
                        db.pkusz.insert_one(result)
                    case "清华大学深圳国际研究生院":
                        # info.university = "深圳大学"
                        db.tsinghua.insert_one(result)
                    case "深圳信息职业技术学院":
                        # info.university = "深圳技术大学"
                        db.sziit.insert_one(result)
                    case "深圳湾实验室":
                        # info.university = "深圳国际量子研究院"
                        db.szbl.insert_one(result)
                    case "深圳北理莫斯科大学":
                        # info.university = "深圳综合粒子设施研究院"
                        db.smbu.insert_one(result)
                    case "北京理工大学深圳汽车研究院":
                        # info.university = "深圳综合粒子设施研究院"
                        db.szari.insert_one(result)


# 只插入大学的表

# 1. 根据项目标题或者采购单位名称判断
# 2. 判断是否属于货物类项目

async def insert_info_to_university_table(info: BiddingInfo) -> bool:

    db = await get_database()

    full_info = scrape_full_infomation(base_url + info.url)

    if not check_date(info.publish_date):
        return False

    # 如果是重点高校，则插入对应的表
    for keyword in [
        "南方科技大学",
        "深圳大学",
        "深圳技术大学",
        "深圳国际量子研究院",
        "深圳综合粒子设施研究院",
        "北京大学深圳研究生院",
        "清华大学深圳国际研究生院",
        "深圳信息职业技术学院",
        "深圳湾实验室",
        "深圳北理莫斯科大学",
        "北京理工大学深圳汽车研究院"
    ]:

        if keyword in info.title or keyword in full_info['采购单位']:

            # 判断该项目是否属于货物类项目
            completion = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                stream=False,
                messages=[
                    {"role": "system", "content": "你是一位招标采购专家，请根据我提供的招标项目描述信息，判断这个项目是否属于货物类项目。"},
                    {"role": "user", "content": f"以下是项目描述：\n"
                                    f"项目名称：{full_info['项目名称']}\n"
                                    f"采购品目：{full_info['采购品目']}\n"
                                    f"采购需求概况：{full_info['采购需求概况']}\n"
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
                    db.nkd_new.insert_one(info.model_dump())
                case "深圳大学":
                    if '总医院' not in info.title and '附属中学' not in info.title and '附属华南医院' not in info.title:
                        db.szu_new.insert_one(info.model_dump())
                case "深圳技术大学":
                    db.sztu_new.insert_one(info.model_dump())
                case "深圳国际量子研究院":
                    db.siqse_new.insert_one(info.model_dump())
                case "深圳综合粒子设施研究院":
                    db.iasf_new.insert_one(info.model_dump())
                case "北京大学深圳研究生院":
                    db.pkusz_new.insert_one(info.model_dump())
                case "清华大学深圳国际研究生院":
                    db.tsinghua_new.insert_one(info.model_dump())
                case "深圳信息职业技术学院":
                    db.sziit_new.insert_one(info.model_dump())
                case "深圳湾实验室":
                    db.szbl_new.insert_one(info.model_dump())
                case "深圳北理莫斯科大学":
                    db.smbu_new.insert_one(info.model_dump())
                case "北京理工大学深圳汽车研究院":
                    db.szari_new.insert_one(info.model_dump())

    return True


async def claw_all():

    print("Getting the latest bidding info at {}...".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    count = 100
    
    while True:
        if count == 1:
            url = first_page_url
        elif count > 100:
            url = page_after_100_url.format(count)
            print("当前url: ", url)
        else:
            url = next_page_url.format(count)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        # response.encoding = 'utf-8'
        # print('response: ', response.text)
        soup = BeautifulSoup(response.text, "html.parser")

        news_items = soup.find('ul', {'class': 'news-items', 'id': 'infoContent'})
        if news_items:
            li_items = news_items.find_all('li')

            for li_item in li_items:
                info = extract_info_from_li_item(li_item)
                if not await insert_info_to_university_table(info):
                    return
        count += 1
        print("已经爬到{}页".format(count))
        await asyncio.sleep(20)  

def crawl_after_100():
    url = "http://zfcg.szggzy.com:8081/EpointWebBuilder/rest/frontAppNotNeedLoginAction/getPageInfoList"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    # {"siteGuid":"","categoryNum":"002001001","pageIndex":"102","pageSize":10,"controlname":"subpagelist","ImgGuid":"4ac6e88a-cd1b-4eb9-afca-eed11da4dd6d","YZM":"r398"}
    params = {
        "siteGuid":"",
        "categoryNum":"002001001",
        "pageIndex":"102",
        "pageSize":10,
        "controlname":"subpagelist",
        "ImgGuid":"63262e91-dc2e-4e00-94ee-b6b4465370ce",
        "YZM":"4gsx"
    }

    response = requests.post(
        url,
        headers=headers,
        params=params
    )
    print('response: ', response.text)

if __name__ == "__main__":
    # asyncio.run(main())
    # specific_info('')
    # asyncio.run(claw_szu_only())
    # specific_info('')
    # asyncio.run(claw_szu_only())
    # crawl_test()
    # asyncio.run(claw_all())
    crawl_after_100()

