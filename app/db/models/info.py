from pydantic import BaseModel


class BiddingInfo(BaseModel):
    title: str
    url: str
    publish_date: str

