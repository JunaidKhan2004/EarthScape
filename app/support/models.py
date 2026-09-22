from datetime import datetime

from bson.objectid import ObjectId

from app import mongo

STATUS_OPEN = "open"
STATUS_RESOLVED = "resolved"


def create_ticket(user_email: str, category: str, message: str) -> str:
    if not message.strip():
        raise ValueError("Message cannot be empty.")

    doc = {
        "user_email": user_email,
        "category": category,
        "message": message.strip(),
        "status": STATUS_OPEN,
        "created_at": datetime.utcnow(),
        "resolved_at": None,
        "response": None,
    }
    result = mongo.db.support_tickets.insert_one(doc)
    return str(result.inserted_id)


def list_tickets_for_user(user_email: str) -> list[dict]:
    return list(mongo.db.support_tickets.find({"user_email": user_email}).sort("created_at", -1))


def list_all_tickets() -> list[dict]:
    return list(mongo.db.support_tickets.find().sort("created_at", -1))


def resolve_ticket(ticket_id: str, response: str) -> None:
    mongo.db.support_tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": {"status": STATUS_RESOLVED, "response": response, "resolved_at": datetime.utcnow()}},
    )
