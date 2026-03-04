from fastapi import HTTPException
from config.mongodb import get_db
from bson import ObjectId
import datetime
from typing import List, Optional

db = get_db()
history_collection = db.analysis_history


async def save_analysis(user_id: str, job_role: str, analysis_data: dict):
    """
    Saves the analysis result to MongoDB.
    """
    record = {
        "user_id": user_id,
        "job_role": job_role,
        "candidate_name": analysis_data.get("extracted", {}).get(
            "candidate_name", "Unknown"
        ),
        "analysis": analysis_data,
        "timestamp": datetime.datetime.utcnow(),
    }

    result = history_collection.insert_one(record)
    return str(result.inserted_id)


async def get_user_history(user_id: str):
    """
    Retrieves all past analysis reports for a specific user.
    """
    cursor = history_collection.find({"user_id": user_id}).sort("timestamp", -1)
    history = []
    for doc in cursor:
        history.append(
            {
                "id": str(doc["_id"]),
                "job_role": doc["job_role"],
                "candidate_name": doc.get(
                    "candidate_name",
                    doc["analysis"]
                    .get("extracted", {})
                    .get("candidate_name", "Unknown"),
                ),
                "score": doc["analysis"].get("score"),
                "recommendation": doc["analysis"].get("recommendation"),
                "timestamp": (
                    doc["timestamp"].isoformat()
                    if isinstance(doc["timestamp"], datetime.datetime)
                    else str(doc["timestamp"])
                ),
            }
        )
    return history


async def get_analysis_by_id(analysis_id: str):
    """
    Retrieves a specific analysis report by its ID.
    """
    try:
        doc = history_collection.find_one({"_id": ObjectId(analysis_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Analysis report not found")

        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "job_role": doc["job_role"],
            "analysis": doc["analysis"],
            "timestamp": (
                doc["timestamp"].isoformat()
                if isinstance(doc["timestamp"], datetime.datetime)
                else str(doc["timestamp"])
            ),
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
