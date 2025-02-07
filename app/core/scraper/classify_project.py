# 招标项目分类 

import asyncio
import requests
from bs4 import BeautifulSoup

import langchain
from openai import OpenAI

from app.core.scraper.main import get_database

prefix = 'http://zfcg.szggzy.com:8081/'

api_key = 'sk-vUyp1vFsIO0OxaIi0c8573Ed7e5e4e18A58618378eE9D106'
openai_url = 'https://openkey.cloud/v1'


client = OpenAI(api_key=api_key, base_url="https://openkey.cloud/v1")

async def get_all_szu_project():

    db = await get_database()

    cursor = db.szu.find()
    results = await cursor.to_list(length=None)
    for result in results:
        # print(result)
        full_url = prefix + result['url']
        # print(result['title'] + ": " + full_url)
        data = scrape_full_infomation(full_url)
        print(data['项目名称'])
        print(data['采购品目'])
        print(data['采购需求概况'])

        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            stream=False,
             messages=[
        {"role": "system", "content": "你是一位招标采购专家，请根据我提供的招标项目描述信息，判断这个项目是否属于货物类项目。"},
        {"role": "user", "content": f"以下是项目描述：\n"
                                   f"项目名称：{data['项目名称']}\n"
                                   f"采购品目：{data['采购品目']}\n"
                                   f"采购需求概况：{data['采购需求概况']}\n"
                                   f"你只需要回复'是'或者'否'"}
    ]
        )
        print("是否属于服务类项目：",completion.choices[0].message.content)
        print("-----------------------------------------------")


def scrape_full_infomation(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

     # 查找包含表格的 div
    contentbox = soup.find("div", class_="contentbox")
    if not contentbox:
        raise ValueError("未找到包含表格的 div")

    # 查找表格
    table = contentbox.find("table", class_="table-style")
    if not table:
        raise ValueError("未找到表格")

    # 提取表格内容
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        # 获取每一行的标题和内容
        cells = row.find_all("td")
        if len(cells) == 2:  # 确保有两列
            key = cells[0].text.strip().replace(":", "")  # 去掉冒号和空白
            value = cells[1].text.strip()
            data[key] = value

    return data



if __name__ == "__main__":
    asyncio.run(get_all_szu_project())