from __future__ import annotations

import os
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId
from gridfs import GridFS
from pymongo import MongoClient


class MongoRepository:
    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is missing. Add it to .env and restart the app.")
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        self.client.admin.command("ping")
        self.db = self.client[os.getenv("MONGODB_DATABASE", "preppilot")]
        self.files = GridFS(self.db)
        self.db.sessions.create_index("created_at")
        self.db.sessions.create_index([("user_id", 1), ("created_at", -1)])
        self.db.evaluations.create_index([("session_id", 1), ("created_at", -1)])
        self.db.users.create_index("email", unique=True)
        self.persistent = True

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _password_hash(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 310_000).hex()

    def create_user(self, name: str, email: str, password: str) -> dict[str, str]:
        normalized_email = email.strip().lower()
        if self.db.users.find_one({"email": normalized_email}):
            raise ValueError("An account with that email already exists.")
        salt = secrets.token_hex(16)
        user = {
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": self._password_hash(password, salt),
            "password_salt": salt,
            "created_at": self._now(),
        }
        user_id = self.db.users.insert_one(user).inserted_id
        return {"id": str(user_id), "name": user["name"], "email": user["email"]}

    def authenticate_user(self, email: str, password: str) -> dict[str, str] | None:
        user = self.db.users.find_one({"email": email.strip().lower()})
        if not user or not secrets.compare_digest(
            user["password_hash"], self._password_hash(password, user["password_salt"])
        ):
            return None
        return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}

    def create_session(self, resume_name: str, resume_bytes: bytes, resume_text: str, jd_text: str, role: str, company: str, plan: dict, user_id: str | None = None) -> str:
        resume_file_id = self.files.put(resume_bytes, filename=resume_name, content_type="application/pdf")
        doc = {"resume_file_id": resume_file_id, "resume_name": resume_name, "resume_text": resume_text, "job_description": jd_text, "role": role, "company": company, "user_id": user_id, **plan, "created_at": self._now()}
        return str(self.db.sessions.insert_one(doc).inserted_id)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self.db.sessions.find_one({"_id": ObjectId(session_id)})

    def recent_sessions(self, user_id: str | None = None) -> list[dict[str, Any]]:
        query = {"user_id": user_id} if user_id else {}
        return list(self.db.sessions.find(query, {"resume_text": 0, "job_description": 0}).sort("created_at", -1).limit(10))

    def add_evaluation(self, session_id: str, question: str, answer: str, result: dict) -> None:
        self.db.evaluations.insert_one({"session_id": session_id, "question": question, "answer": answer, **result, "created_at": self._now()})

    def evaluations(self, session_id: str) -> list[dict[str, Any]]:
        return list(self.db.evaluations.find({"session_id": session_id}, {"_id": 0}).sort("created_at", -1))

    def add_question(self, session_id: str, question: str) -> None:
        self.db.sessions.update_one({"_id": ObjectId(session_id)}, {"$addToSet": {"questions": question}})


class InMemoryRepository:
    """Temporary repository used when Atlas cannot be reached.

    It keeps the complete interview workflow available, but data is lost when
    the Streamlit process restarts.
    """

    persistent = False

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._evaluations: dict[str, list[dict[str, Any]]] = {}
        self._users: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_user(self, name: str, email: str, password: str) -> dict[str, str]:
        normalized_email = email.strip().lower()
        if any(user["email"] == normalized_email for user in self._users.values()):
            raise ValueError("An account with that email already exists.")
        user_id = str(uuid4())
        self._users[user_id] = {"id": user_id, "name": name.strip(), "email": normalized_email, "password": password}
        return {key: self._users[user_id][key] for key in ("id", "name", "email")}

    def authenticate_user(self, email: str, password: str) -> dict[str, str] | None:
        normalized_email = email.strip().lower()
        for user in self._users.values():
            if user["email"] == normalized_email and secrets.compare_digest(user["password"], password):
                return {key: user[key] for key in ("id", "name", "email")}
        return None

    def create_session(self, resume_name: str, resume_bytes: bytes, resume_text: str, jd_text: str, role: str, company: str, plan: dict, user_id: str | None = None) -> str:
        session_id = str(uuid4())
        self._sessions[session_id] = {
            "_id": session_id,
            "resume_name": resume_name,
            "resume_text": resume_text,
            "job_description": jd_text,
            "role": role,
            "company": company,
            "user_id": user_id,
            **plan,
            "created_at": self._now(),
        }
        self._evaluations[session_id] = []
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    def recent_sessions(self, user_id: str | None = None) -> list[dict[str, Any]]:
        sessions = self._sessions.values()
        if user_id:
            sessions = (session for session in sessions if session.get("user_id") == user_id)
        return sorted(sessions, key=lambda session: session["created_at"], reverse=True)[:10]

    def add_evaluation(self, session_id: str, question: str, answer: str, result: dict) -> None:
        self._evaluations.setdefault(session_id, []).insert(
            0,
            {"session_id": session_id, "question": question, "answer": answer, **result, "created_at": self._now()},
        )

    def evaluations(self, session_id: str) -> list[dict[str, Any]]:
        return self._evaluations.get(session_id, [])

    def add_question(self, session_id: str, question: str) -> None:
        session = self._sessions.get(session_id)
        if session and question not in session["questions"]:
            session["questions"].append(question)
