import asyncio
import json

import pandas as pd 
from app.db.models.info import BiddingInfo
from app.db.mongodb import get_database

import datetime

from openai import OpenAI

api_key = 'sk-vUyp1vFsIO0OxaIi0c8573Ed7e5e4e18A58618378eE9D106'
openai_url = 'https://openkey.cloud/v1'

client = OpenAI(api_key=api_key, base_url="https://openkey.cloud/v1")

df = pd.read_excel('bidding_information.xlsx', sheet_name='采购意向项目列表', skiprows=1)

print(df.columns)

#Index(['项目名称', '采购单位', '预算金额', '采购品目', '采购需求概况', '预计采购时间', '发布时间', '备注'], dtype='object')
'''       
       1 "深圳医学科学院", szyxkxy
       2 "哈尔滨工业大学（深圳）", hgd
       3 "香港中文大学（深圳）", hkc
       4 "深圳理工大学", szlg
       5 "深圳职业技术大学", szzyjs
       6 "深圳综合粒子设施研究院", iasf
       7 "鹏城实验室" pcsys
       8 "" 
'''

def filter_after_date(df, date_str) -> pd.DataFrame:
    # 将“发布时间”列转换为日期格式
    df['发布时间'] = pd.to_datetime(df['发布时间'], errors='coerce')  # 处理无法转换的情况

    # 将输入的日期字符串转换为日期格式
    target_date = pd.to_datetime(date_str)

    # 筛选出“发布时间”在指定日期之后的行
    filtered_df = df[df['发布时间'] > target_date]

    return filtered_df


async def insert_db(info: BiddingInfo, university: str):
    db = await get_database()

    match university:
        case "鹏城实验室":
            university = "pcsys"
        case _:
            university = "unknown"

    collection = db[university]
    await collection.insert_one(info.model_dump())


async def main():

    filtered_df_1 = filter_after_date(df[df['采购单位'] == '鹏城实验室'], '2024-10-31')


    total_filtered_df = pd.concat([filtered_df_1])


    for index, row in total_filtered_df.iterrows():
        print('发布时间：', row['发布时间'])
        info = BiddingInfo(
            title=row['项目名称'],
            publish_date=row['发布时间'].strftime('%Y-%m-%d'),
            is_good=False,
            url='',
            created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 判断是否是货物类项目
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            stream=False,
            messages=[
                {"role": "system", "content": "你是一位招标采购专家，请根据我提供的招标项目描述信息，判断这个项目是否属于货物类项目。"},
                {"role": "user", "content": f"以下是项目描述：\n"
                                f"项目名称：{row['项目名称']}\n"
                                f"采购品目：{row['采购品目']}\n"
                                f"采购需求概况：{row['采购需求概况']}\n"
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

        # 将信息插入到数据库中
        await insert_db(info, row['采购单位'])



if __name__ == "__main__":
    asyncio.run(main())