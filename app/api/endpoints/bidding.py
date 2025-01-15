from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime

from app.db.mongodb import get_database
from app.db.models.info import BiddingInfo

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
    
    count = await db.bidding_info.count_documents(query)
    return {"total": count}

