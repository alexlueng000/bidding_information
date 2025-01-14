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
    db = await get_database()
    query = {}
    
    # Add date filter if provided
    if date:
        query["publish_date"] = date
    
    cursor = db.bidding_info.find(query).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    
    return results