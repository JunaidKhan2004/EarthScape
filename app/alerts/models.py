from datetime import datetime

from bson.objectid import ObjectId

from app import mongo


def create_threshold(source_type: str, metric: str, operator: str, value: float, created_by: str) -> str:
    if operator not in (">", "<", ">=", "<="):
        raise ValueError("operator must be one of >, <, >=, <=")

    doc = {
        "source_type": source_type,
        "metric": metric,
        "operator": operator,
        "value": value,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "active": True,
    }
    result = mongo.db.alert_thresholds.insert_one(doc)
    return str(result.inserted_id)


def list_thresholds(active_only: bool = True) -> list[dict]:
    query = {"active": True} if active_only else {}
    return list(mongo.db.alert_thresholds.find(query).sort("created_at", -1))


def deactivate_threshold(threshold_id: str) -> None:
    mongo.db.alert_thresholds.update_one(
        {"_id": ObjectId(threshold_id)}, {"$set": {"active": False}}
    )


def _breaches(operator: str, value: float, threshold: float) -> bool:
    return {
        ">": value > threshold,
        "<": value < threshold,
        ">=": value >= threshold,
        "<=": value <= threshold,
    }[operator]


def record_triggered_alert(threshold: dict, group_key: str, observed_value: float, timestamp: str) -> None:
    mongo.db.triggered_alerts.insert_one({
        "threshold_id": threshold["_id"],
        "source_type": threshold["source_type"],
        "metric": threshold["metric"],
        "operator": threshold["operator"],
        "threshold_value": threshold["value"],
        "group_key": group_key,
        "observed_value": observed_value,
        "record_timestamp": timestamp,
        "triggered_at": datetime.utcnow(),
        "acknowledged": False,
    })


def evaluate_thresholds_against_groups(source_type: str, groups: list[dict]) -> int:
    """Check the latest MapReduce group stats (mean value per group) against
    active thresholds for this source_type. Records a triggered_alert per breach.
    Returns the number of new alerts triggered."""
    thresholds = [t for t in list_thresholds(active_only=True) if t["source_type"] == source_type]
    if not thresholds:
        return 0

    triggered_count = 0
    for group in groups:
        for threshold in thresholds:
            if _breaches(threshold["operator"], group["mean"], threshold["value"]):
                record_triggered_alert(threshold, group["group_key"], group["mean"], group.get("generated_at", ""))
                triggered_count += 1

    return triggered_count


def list_triggered_alerts(limit: int = 50) -> list[dict]:
    return list(mongo.db.triggered_alerts.find().sort("triggered_at", -1).limit(limit))


def acknowledge_alert(alert_id: str) -> None:
    mongo.db.triggered_alerts.update_one(
        {"_id": ObjectId(alert_id)}, {"$set": {"acknowledged": True}}
    )
