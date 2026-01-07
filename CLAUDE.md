# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A bidding information collection platform (招标信息收集平台 v0.1) that scrapes procurement notices from Chinese government websites and stores them in MongoDB. The platform provides a FastAPI backend to serve this data to a frontend.

**Data Sources:**
- Shenzhen Government Procurement (深圳政府采购网) - primary source
- Other platforms: 易采通, 云采通

**Target Institutions:**
The system tracks bidding information for 18+ universities and research institutes in Shenzhen, including:
- 南方科技大学 (nkd), 深圳大学 (szu), 深圳技术大学 (sztu)
- 深圳国际量子研究院 (siqse), 深圳先进光源研究院 (iasf)
- 北京大学深圳研究生院 (pkusz), 清华大学深圳国际研究生院 (tsinghua)
- And 10+ others (see `app/core/scraper/main.py` for full list)

## Development Commands

**Run the FastAPI server:**
```bash
# Activate virtual environment first (if needed)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run with uvicorn
uvicorn app.main:app --reload
```

**Run the scraper:**
```bash
python -m app.core.scraper.main
```

**Test database connection:**
```bash
python -m app.tests.test_database_connection
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Architecture

### Directory Structure

```
app/
├── main.py              # FastAPI app entry point, CORS, router registration
├── api/
│   ├── endpoints/
│   │   └── bidding.py   # API routes for fetching bidding data
│   ├── models/
│   │   └── response.py  # Pydantic response models
│   └── schemas/         # (currently empty)
├── core/
│   ├── config.py        # App settings (metadata, database URL)
│   ├── scraper/
│   │   ├── main.py      # Main scraper logic with APScheduler
│   │   └── scrape_full_info.py  # Detail page scraping
│   └── security.py      # (empty)
└── db/
    ├── mongodb.py       # Motor async MongoDB client setup
    └── models/
        └── info.py      # BiddingInfo Pydantic model
```

### Key Components

**1. Scraper (`app/core/scraper/main.py`)**
- `get_shenzhen_bidding_info()`: Main scraping loop, paginates through listing pages
- `insert_info_to_db()`: Inserts records and classifies by university keywords
- Uses APScheduler with CronTrigger for scheduled runs (8, 12, 16, 20 hours)
- Uses OpenAI API to classify projects as "goods" (货物类)
- Proxies rotation for anti-blocking

**2. API Endpoints (`app/api/endpoints/bidding.py`)**
- `GET /api/v1/bidding` - List all bidding info (paginated, optional date filter)
- `GET /api/v1/bidding/count` - Total count of bidding records
- `GET /api/v1/bidding/universities` - Summary for all universities (5 items each + totals)
- `GET /api/v1/bidding/universities/{university}` - All records for specific university

**3. Database (`app/db/mongodb.py`)**
- Uses Motor (async MongoDB driver)
- Default: `mongodb://localhost:27017`, database: `bidding`
- Collections: `bidding_infomation` (main), plus one per university (nkd, szu, sztu, etc.)

### Data Flow

1. Scraper fetches listing pages from `zfcg.szggzy.com:8081`
2. For each new item, fetches detail page for full project info
3. Checks title/organization against 18+ university keywords
4. Calls OpenAI API to determine if project is "goods" (货物类)
5. Inserts into main collection + university-specific collection if matched

### Environment Variables

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_key_here
```

The OpenAI API is used for project classification (货物类 determination).

## Important Notes

**University Classification Logic:**
- Some universities have exclusion filters (e.g., 深圳大学 excludes "总医院", "附属中学", "附属华南医院")
- See the match/case block in `insert_info_to_db()` (line 282-320 in main.py)

**Date Filtering:**
- `check_date()` function filters records after 2024-10-31
- Scraping stops when it encounters records before this date

**Database Collection Names:**
The main collection is `bidding_infomation` (note: "information" is misspelled in the original code - keep this for compatibility).
