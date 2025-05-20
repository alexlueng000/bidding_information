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
    
    nkd = await db.nkd.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    nkd_total = await db.nkd.count_documents({"is_good": True})
    szu = await db.szu.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szu_total = await db.szu.count_documents({"is_good": True})
    # print("深圳大学总项目数：", szu_total)
    sztu = await db.sztu.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    sztu_total = await db.sztu.count_documents({"is_good": True})
    iasf = await db.iasf.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    iasf_total = await db.iasf.count_documents({"is_good": True})
    siqse = await db.siqse.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    siqse_total = await db.siqse.count_documents({"is_good": True})
    pkusz = await db.pkusz.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    pkusz_total = await db.pkusz.count_documents({"is_good": True})
    tsinghua = await db.tsinghua.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    tsinghua_total = await db.tsinghua.count_documents({"is_good": True})
    sziit = await db.sziit.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    sziit_total = await db.sziit.count_documents({"is_good": True})
    szbl = await db.szbl.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szbl_total = await db.szbl.count_documents({"is_good": True})
    smbu = await db.smbu.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    smbu_total = await db.smbu.count_documents({"is_good": True})
    szari = await db.szari.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szari_total = await db.szari.count_documents({"is_good": True})
    szyxkxy = await db.szyxkxy.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szyxkxy_total = await db.szyxkxy.count_documents({"is_good": True})
    hgd = await db.hgd.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    hgd_total = await db.hgd.count_documents({"is_good": True})
    hkc = await db.hkc.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    hkc_total = await db.hkc.count_documents({"is_good": True})
    szlg = await db.szlg.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szlg_total = await db.szlg.count_documents({"is_good": True})
    szust = await db.szust.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szust_total = await db.szust.count_documents({"is_good": True})
    szzyjs = await db.szzyjs.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    szzyjs_total = await db.szzyjs.count_documents({"is_good": True})
    pcsys = await db.pcsys.find({"is_good": True}).sort("publish_date", -1).skip(0).limit(5).to_list(length=5)
    pcsys_total = await db.pcsys.count_documents({"is_good": True})

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
        siqse_total=siqse_total,
        pkusz=pkusz,
        pkusz_total=pkusz_total,
        tsinghua=tsinghua,
        tsinghua_total=tsinghua_total,
        sziit=sziit,
        sziit_total=sziit_total,
        szbl=szbl,
        szbl_total=szbl_total,
        smbu=smbu,
        smbu_total=smbu_total,
        szari=szari,
        szari_total=szari_total,
        szyxkxy=szyxkxy,
        szyxkxy_total=szyxkxy_total,
        hgd=hgd,
        hgd_total=hgd_total,
        hkc=hkc,
        hkc_total=hkc_total,
        szlg=szlg,
        szlg_total=szlg_total,
        szzyjs=szzyjs,
        szzyjs_total=szzyjs_total,
        pcsys=pcsys,
        pcsys_total=pcsys_total,
        szust=szust,
        szust_total=szust_total
    )
    return response

@router.get("/bidding/universities/{university}", response_model=List[BiddingInfo])
async def get_university_info_by_university(university: str):
    
    print("the university that query: ", university)
    
    db = await get_database()
    collection = db[university]
    if collection is not None:
        cursor = collection.find({"is_good": True}).sort("publish_date", -1)
        results = await cursor.to_list()
        return results
    else:
        return None
