from pydantic import BaseModel
from typing import List

class UniversityInfo(BaseModel):
    title: str
    url: str
    publish_date: str
    created_at: str


class UniversityInfoList(BaseModel):
    universities: List[UniversityInfo]


class UniversityInfoResponse(BaseModel):
    iasf: List[UniversityInfo]
    iasf_total: int
    nkd: List[UniversityInfo]
    nkd_total: int
    sztu: List[UniversityInfo]
    sztu_total: int
    szu: List[UniversityInfo]
    szu_total: int
    siqse: List[UniversityInfo]
    siqse_total: int

