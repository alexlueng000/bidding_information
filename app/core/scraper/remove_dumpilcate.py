from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "bidding"

COLLECTIONS_TO_DEDUP = [
    "nkd", "szu", "sztu", "siqse", "iasf", "pkusz", "tsinghua", "sziit",
    "szbl", "smbu", "szari", "szyxkxy", "hgd", "hkc", "szlg", "szzyjs",
    "pcsys", "szust"
]

def remove_duplicates_from_collection(collection):
    print(f"➡️ 处理集合：{collection.name}")
    pipeline = [
        {
            "$group": {
                "_id": {
                    "title": "$title",
                    "url": "$url"
                },
                "min_id": {"$min": "$_id"},
                "dupes": {"$push": "$_id"},
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        }
    ]

    duplicates = list(collection.aggregate(pipeline))
    total_removed = 0

    for group in duplicates:
        dupes = group["dupes"]
        dupes.remove(group["min_id"])
        result = collection.delete_many({"_id": {"$in": dupes}})
        total_removed += result.deleted_count

    print(f"✅ 去重完成：共删除 {total_removed} 条记录\n")
    return total_removed

def deduplicate_all_collections(uri=MONGO_URI, db_name=DB_NAME, collections=COLLECTIONS_TO_DEDUP):
    client = MongoClient(uri)
    db = client[db_name]
    total = 0

    for name in collections:
        collection = db[name]
        total += remove_duplicates_from_collection(collection)

    print(f"🎉 所有集合处理完毕，总共删除 {total} 条重复记录")

deduplicate_all_collections()