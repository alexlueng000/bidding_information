from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class UniversityInfo(BaseModel):
    model_config = ConfigDict(extra='ignore')

    title: str
    publish_date: str
    created_at: Optional[str] = None


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
    pkusz: List[UniversityInfo]
    pkusz_total: int
    tsinghua: List[UniversityInfo]
    tsinghua_total: int
    sziit: List[UniversityInfo]
    sziit_total: int
    szbl: List[UniversityInfo]
    szbl_total: int 
    szari: List[UniversityInfo]
    szari_total: int
    smbu: List[UniversityInfo]
    smbu_total: int
    pcsys: List[UniversityInfo]
    pcsys_total: int
    szyxkxy: List[UniversityInfo]
    szyxkxy_total: int
    hgd: List[UniversityInfo]
    hgd_total: int
    hkc: List[UniversityInfo]
    hkc_total: int
    szlg: List[UniversityInfo]
    szlg_total: int
    szzyjs: List[UniversityInfo]
    szzyjs_total: int
    szust: List[UniversityInfo]
    szust_total: int

    
    

