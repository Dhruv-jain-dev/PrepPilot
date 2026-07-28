from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from gridfs import GridFS
from pymongo import MongoClient


class MongoRepository:
    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is missing. Add it to .env and restart the app.")
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.client.admin.command("ping")
        self.db = self.client[os.getenv("MONGODB_DATABASE", "preppilot")]
        self.files = GridFS(self.db)
        self.db.sessions.create_index("created_at")
        self.db.evaluations.create_index([("session_id", 1), ("created_at", -1)])

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_session(self, resume_name: str, resume_bytes: bytes, resume_text: str, jd_text: str, role: str, company: str, plan: dict) -> str:
        resume_file_id = self.files.put(resume_bytes, filename=resume_name, content_type="application/pdf")
        doc = {"resume_file_id": resume_file_id, "resume_name": resume_name, "resume_text": resume_text, "job_description": jd_text, "role": role, "company": company, **plan, "created_at": self._now()}
        return str(self.db.sessions.insert_one(doc).inserted_id)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self.db.sessions.find_one({"_id": ObjectId(session_id)})

    def recent_sessions(self) -> list[dict[str, Any]]:
        return list(self.db.sessions.find({}, {"resume_text": 0, "job_description": 0}).sort("created_at", -1).limit(10))

    def add_evaluation(self, session_id: str, question: str, answer: str, result: dict) -> None:
        self.db.evaluations.insert_one({"session_id": session_id, "question": question, "answer": answer, **result, "created_at": self._now()})

    def evaluations(self, session_id: str) -> list[dict[str, Any]]:
        return list(self.db.evaluations.find({"session_id": session_id}, {"_id": 0}).sort("created_at", -1))
