from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from typing import List, Optional, Dict
from datetime import datetime

from app.db.mongodb import get_database
from app.db.models.info import BiddingInfo
from app.api.models.response import UniversityInfoResponse

router = APIRouter()

@router.get("/bidding", response_model=List[BiddingInfo])
async def get_bidding_info(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100),
    date: Optional[str] = None
):
    print("skip: ", skip)
    print("limit: ", limit)
    # print("date: ", date)
    
    db = await get_database()
    query = {}
    
    # Add date filter if provided
    if date:
        query["publish_date"] = date
    
    cursor = db.bidding_infomation.find(query).sort("publish_date", -1).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    
    return results


@router.get("/bidding/count")
async def get_bidding_info_count(
    date: Optional[str] = None
):
    db = await get_database()
    query = {}
    if date:
        query = {"publish_date": date}
    
    count = await db.bidding_infomation.count_documents(query)
    return {"total": count}


@router.get("/bidding/universities", response_model=UniversityInfoResponse)
async def get_university_info():
    
    db = await get_database()
    
    nkd = await db.nkd.find().sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    nkd_total = await db.nkd.count_documents({})
    szu = await db.szu.find().sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szu_total = await db.szu.count_documents({})
    print("深圳大学总项目数：", szu_total)
    sztu = await db.sztu.find().sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    sztu_total = await db.sztu.count_documents({})
    iasf = await db.iasf.find().sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    iasf_total = await db.iasf.count_documents({})
    siqse = await db.siqse.find().sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    siqse_total = await db.siqse.count_documents({})


    response = UniversityInfoResponse(
        iasf=iasf,
        iasf_total=iasf_total,
        nkd=nkd,
        nkd_total=nkd_total,
        sztu=sztu,
        sztu_total=sztu_total,
        szu=szu,
        szu_total=szu_total,
        siqse=siqse,
        siqse_total=siqse_total
    )
    return response

@router.get("/bidding/universities/{university}", response_model=List[BiddingInfo])
async def get_university_info_by_university(university: str):
    
    print("the university that query: ", university)
    
    db = await get_database()
    collection = db[university]
    if collection is not None:
        cursor = collection.find().sort("publish_date", -1)
        results = await cursor.to_list()
        return results
    else:
        return None
