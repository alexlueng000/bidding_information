import asyncio
import json
from typing import Optional, Dict

import pandas as pd
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

from app.db.mongodb import get_database

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://openkey.cloud/v1")

# University keyword to collection name mapping
UNIVERSITY_KEYWORDS = {
    "南方科技大学": "nkd",
    "深圳大学": "szu",
    "深圳技术大学": "sztu",
    "深圳国际量子研究院": "siqse",
    "深圳先进光源研究院": "iasf",
    "北京大学深圳研究生院": "pkusz",
    "清华大学深圳国际研究生院": "tsinghua",
    "深圳信息职业技术学院": "sziit",
    "深圳湾实验室": "szbl",
    "深圳北理莫斯科大学": "smbu",
    "北京理工大学深圳汽车研究院": "szari",
    "深圳医学科学院": "szyxkxy",
    "哈尔滨工业大学（深圳）": "hgd",
    "香港中文大学（深圳）": "hkc",
    "深圳理工大学": "szlg",
    "深圳职业技术大学": "szzyjs",
    "鹏城实验室": "pcsys",
    "中山大学深圳校区": "szust"
}

# Column name mapping: Chinese -> English
COLUMN_MAPPING = {
    '项目名称': 'title',
    '采购单位': 'organization',
    '预算金额': 'budget',
    '采购品目': 'category',
    '采购需求概况': 'description',
    '预计采购时间': 'expected_time',
    '发布时间': 'publish_date',
    '备注': 'remarks'
}


def filter_after_date(df: pd.DataFrame, date_str: str, date_column: str = '发布时间') -> pd.DataFrame:
    """Filter rows where date_column is after the given date."""
    df_copy = df.copy()
    df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
    target_date = pd.to_datetime(date_str)
    return df_copy[df_copy[date_column] > target_date]


def classify_university(title: str, organization: str) -> Optional[str]:
    """
    Classify which university this project belongs to based on title and organization.
    Returns the collection name or None.
    """
    for keyword, collection_name in UNIVERSITY_KEYWORDS.items():
        if keyword in title or keyword in organization:
            # Special handling for 深圳大学
            if keyword == "深圳大学":
                if '总医院' not in title and '附属中学' not in title and '附属华南医院' not in title:
                    return collection_name
            # Special handling for 南方科技大学
            elif keyword == "南方科技大学":
                if '南方科技大学医院' != organization:
                    return collection_name
            else:
                return collection_name
    return None


def row_to_dict_with_mapping(row: pd.Series) -> Dict[str, any]:
    """Convert pandas Series to dict, mapping Chinese column names to English."""
    result = {}
    for key, value in row.items():
        if pd.isna(value):
            mapped_value = None
        elif isinstance(value, pd.Timestamp):
            mapped_value = str(value)
        elif isinstance(value, (np.integer, np.floating)):
            mapped_value = int(value) if isinstance(value, np.integer) else float(value)
        else:
            mapped_value = value

        # Map Chinese column names to English
        english_key = COLUMN_MAPPING.get(key, key)
        result[english_key] = mapped_value
    return result


async def insert_info_to_db_from_excel(row_data: Dict[str, any]) -> bool:
    """
    Insert bidding info from Excel into database using the same logic as web scraper.
    Stores data with English field names.

    Args:
        row_data: Dictionary containing all column values from Excel row (with English keys)

    Returns:
        bool: True if inserted, False if skipped (duplicate)
    """
    import datetime

    db = await get_database()

    # Extract key fields for duplicate check
    title = row_data.get('title', '')
    publish_date = row_data.get('publish_date', '')

    # Check if already exists (by title + publish_date)
    query = {
        "title": title,
        "publish_date": publish_date
    }
    exist_info = await db.bidding_infomation.find_one(query)
    if exist_info:
        print(f"[insert_from_excel] ⏭️  Already exists: {title}")
        return False

    # Add metadata fields
    row_data['created_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure publish_date is string format
    if isinstance(row_data.get('publish_date'), pd.Timestamp):
        row_data['publish_date'] = row_data['publish_date'].strftime('%Y-%m-%d')

    # Insert into main table
    await db.bidding_infomation.insert_one(row_data)
    print(f"[insert_from_excel] ✅ Inserted to main table: {title}")

    # Classify by university
    organization = row_data.get('organization', '')
    collection_name = classify_university(title, organization)
    if not collection_name:
        print(f"[insert_from_excel] ⏭️  No university match, skipping: {title}")
        return True

    # Use OpenAI to determine if it's a "goods" (货物类) project
    project_name = row_data.get('title', '')
    category = row_data.get('category', '')
    description = row_data.get('description', '')

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            stream=False,
            messages=[
                {"role": "system", "content": "你是一位招标采购专家，请根据我提供的招标项目描述信息，判断这个项目是否属于货物类项目。"},
                {"role": "user", "content": f"以下是项目描述：\n"
                                f"项目名称：{project_name}\n"
                                f"采购品目：{category}\n"
                                f"采购需求概况：{description}\n"
                                "请用JSON格式回复'true'或者'false':{is_good: ...}"}
            ],
            response_format={"type": "json_object"}
        )

        response_data = json.loads(completion.choices[0].message.content)
        is_good = response_data.get("is_good", False)
    except (json.JSONDecodeError, Exception) as e:
        print(f"[insert_from_excel] ⚠️  OpenAI API error: {e}")
        is_good = False

    # Add is_good field
    row_data['is_good'] = is_good

    # Insert into university-specific collection
    collection = db[collection_name]
    await collection.insert_one(row_data)
    print(f"[insert_from_excel] ✅ Inserted to {collection_name}: {title} (is_good={is_good})")

    return True


async def process_from_excel(
    file_path: str = 'projects.xlsx',
    sheet_name: str = '采购意向项目列表',
    skiprows: int = 1,
    after_date: str = '2025-5-31',
    date_column: str = '发布时间'
):
    """
    Process bidding information from local Excel file and insert into database.
    Stores data with English field names.

    Args:
        file_path: Path to the Excel file
        sheet_name: Sheet name in the Excel file
        skiprows: Number of rows to skip from the top
        after_date: Only process records where date_column is after this date
        date_column: Column name to use for date filtering
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)
        print(f"[process_from_excel] 📖 Loaded {len(df)} rows from {file_path}")
    except FileNotFoundError:
        print(f"[process_from_excel] ❌ File not found: {file_path}")
        return
    except Exception as e:
        print(f"[process_from_excel] ❌ Error reading Excel: {e}")
        return

    print(f"[process_from_excel] 📋 Columns found: {list(df.columns)}")

    # Filter by date
    if date_column in df.columns:
        filtered_df = filter_after_date(df, after_date, date_column)
        print(f"[process_from_excel] 📅 Filtered to {len(filtered_df)} rows after {after_date}")
    else:
        print(f"[process_from_excel] ⚠️  Date column '{date_column}' not found, using all rows")
        filtered_df = df.copy()

    # Process each row
    success_count = 0
    skip_count = 0

    for index, row in filtered_df.iterrows():
        # Convert row to dict with English field names
        row_data = row_to_dict_with_mapping(row)

        inserted = await insert_info_to_db_from_excel(row_data)
        if inserted:
            success_count += 1
        else:
            skip_count += 1

    print(f"[process_from_excel] ✨ Complete! Inserted: {success_count}, Skipped (duplicates): {skip_count}")


async def main():
    """Example usage."""
    await process_from_excel(
        file_path='projects.xlsx',
        sheet_name='采购意向项目列表',
        skiprows=1,
        after_date='2025-5-31',
        date_column='发布时间'
    )


if __name__ == "__main__":
    asyncio.run(main())
