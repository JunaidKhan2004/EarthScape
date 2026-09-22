from bson.objectid import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import mongo

ROLE_ADMIN = "administrator"
ROLE_ANALYST = "analyst"


class User(UserMixin):
    def __init__(self, user_doc):
        self.doc = user_doc
        self.id = str(user_doc["_id"])
        self.email = user_doc["email"]
        self.name = user_doc.get("name", "")
        self.role = user_doc.get("role", ROLE_ANALYST)

    @staticmethod
    def get_by_id(user_id):
        doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return User(doc) if doc else None

    @staticmethod
    def get_by_email(email):
        doc = mongo.db.users.find_one({"email": email.lower()})
        return User(doc) if doc else None

    @staticmethod
    def list_all():
        return [User(doc) for doc in mongo.db.users.find().sort("email", 1)]

    @staticmethod
    def set_role(user_id, role):
        if role not in (ROLE_ANALYST, ROLE_ADMIN):
            raise ValueError("Invalid role.")
        mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": role}})

    @staticmethod
    def create(email, password, name, role=ROLE_ANALYST):
        if mongo.db.users.find_one({"email": email.lower()}):
            raise ValueError("A user with this email already exists.")

        doc = {
            "email": email.lower(),
            "password_hash": generate_password_hash(password),
            "name": name,
            "role": role,
        }
        result = mongo.db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return User(doc)

    def check_password(self, password):
        return check_password_hash(self.doc["password_hash"], password)

    def set_password(self, new_password):
        password_hash = generate_password_hash(new_password)
        mongo.db.users.update_one(
            {"_id": ObjectId(self.id)}, {"$set": {"password_hash": password_hash}}
        )
        self.doc["password_hash"] = password_hash

    def set_name(self, new_name):
        mongo.db.users.update_one({"_id": ObjectId(self.id)}, {"$set": {"name": new_name}})
        self.doc["name"] = new_name
        self.name = new_name

    def is_admin(self):
        return self.role == ROLE_ADMIN
