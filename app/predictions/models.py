from datetime import datetime

from bson.objectid import ObjectId

from app import mongo

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


def create_prediction(source_type: str, metric: str, group_key: str, forecast_result: dict, created_by: str) -> str:
    doc = {
        "source_type": source_type,
        "metric": metric,
        "group_key": group_key,
        "history_days": forecast_result["history_days"],
        "last_observed_value": forecast_result["last_observed_value"],
        "forecast": forecast_result["forecast"],
        "metrics": forecast_result["metrics"],
        "status": STATUS_PENDING,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "reviewed_by": None,
        "reviewed_at": None,
    }
    result = mongo.db.predictions.insert_one(doc)
    return str(result.inserted_id)


def list_predictions(status: str | None = None) -> list[dict]:
    query = {"status": status} if status else {}
    return list(mongo.db.predictions.find(query).sort("created_at", -1))


def list_predictions_for_user(created_by: str) -> list[dict]:
    return list(mongo.db.predictions.find({"created_by": created_by}).sort("created_at", -1))


def get_prediction(prediction_id: str) -> dict | None:
    return mongo.db.predictions.find_one({"_id": ObjectId(prediction_id)})


def review_prediction(prediction_id: str, status: str, reviewed_by: str) -> None:
    if status not in (STATUS_APPROVED, STATUS_REJECTED):
        raise ValueError("status must be approved or rejected")
    mongo.db.predictions.update_one(
        {"_id": ObjectId(prediction_id)},
        {"$set": {"status": status, "reviewed_by": reviewed_by, "reviewed_at": datetime.utcnow()}},
    )


def list_approved_for_public(limit: int = 20) -> list[dict]:
    return list(
        mongo.db.predictions.find({"status": STATUS_APPROVED}).sort("reviewed_at", -1).limit(limit)
    )
