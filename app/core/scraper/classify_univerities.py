# 将招标信息分类到不同的大学
# 南方科技大学、深圳大学、深圳技术大学、深圳国际量子研究院、深圳综合粒子设施研究院
# 存在mongodb中, 每个大学一张表

import asyncio

from typing import Literal
import datetime 


from app.core.scraper.main import get_database
from app.db.models.info import BiddingInfo
from app.core.scraper.main import get_shenzhen_bidding_info
from app.core.scraper.main import get_all_info_from_db

ClassificationResult = Literal[
    "南方科技大学",
    "深圳大学",
    "深圳技术大学",
    "深圳国际量子研究院",
    "深圳综合粒子设施研究院",
    "未分类"
]

async def classify_info(info: BiddingInfo):

    db = await get_database()
    
    info.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for keyword in [
        "南方科技大学",
        "深圳大学",
        "深圳技术大学",
        "深圳国际量子研究院",
        "深圳综合粒子设施研究院",
    ]:
        if keyword in info.title:
            match keyword:
                case "南方科技大学":
                    # info.university = "南方科技大学"
                    db.nkd.insert_one(info.model_dump())
                case "深圳大学":
                    # info.university = "深圳大学"
                    db.szu.insert_one(info.model_dump())
                case "深圳技术大学":
                    # info.university = "深圳技术大学"
                    db.sztu.insert_one(info.model_dump())
                case "深圳国际量子研究院":
                    # info.university = "深圳国际量子研究院"
                    db.siqse.insert_one(info.model_dump())
                case "深圳综合粒子设施研究院":
                    # info.university = "深圳综合粒子设施研究院"
                    db.iasf.insert_one(info.model_dump())



async def classify_exist_info():

    db = await get_database()

    # 南方科技大学
    nkd = []
    # 深圳大学
    szu = []
    # 深圳技术大学
    sztu = []
    # 深圳国际量子研究院
    siqse = []
    # 深圳综合粒子设施研究院
    iasf = []

    all_info = await get_all_info_from_db()

    for info in all_info:
        if "南方科技大学" in info.title:
            nkd.append(info)
            db.nkd.insert_one(info.model_dump())
        elif "深圳大学" in info.title:
            szu.append(info)
            db.szu.insert_one(info.model_dump())
        elif "深圳技术大学" in info.title:
            sztu.append(info)
            db.sztu.insert_one(info.model_dump())
        elif "深圳国际量子研究院" in info.title:
            siqse.append(info)
            db.siqse.insert_one(info.model_dump())
        elif "深圳综合粒子设施研究院" in info.title:
            iasf.append(info)
            db.iasf.insert_one(info.model_dump())
    
    return nkd, szu, sztu, siqse, iasf


async def print_info():
    nkd, szu, sztu, siqse, iasf = await classify_exist_info()
    print("南方科技大学: ", len(nkd))
    for info in nkd:
        print(info.title)
    print("深圳大学: ", len(szu))
    for info in szu:
        print(info.title)
    print("深圳技术大学: ", len(sztu))
    for info in sztu:
        print(info.title)
    print("深圳国际量子研究院: ", len(siqse))
    for info in siqse:
        print(info.title)
    print("深圳综合粒子设施研究院: ", len(iasf))
    for info in iasf:
        print(info.title)
        


if __name__ == "__main__":
    asyncio.run(print_info())


