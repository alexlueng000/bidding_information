from pydantic import BaseModel
from typing import Optional


class BiddingInfo(BaseModel):
    title: str
    url: str
    publish_date: str
    created_at: Optional[str] = None

