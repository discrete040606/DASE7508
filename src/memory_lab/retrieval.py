import json
import time
import uuid
from pathlib import Path

from .models import Session, USERS, digest, write_json


class Sessions:
    """Trusted local session manager; chat/model parameters never create sessions."""
    def __init__(self):
        self._issued = {}

    def create(self, user: str):
        if user not in USERS:
            raise ValueError("Unknown simulated user")
        session = Session(session_id=uuid.uuid4().hex, authenticated_user_id=user)
        self._issued[session.session_id] = session
        return session

    def verify(self, session):
        return isinstance(session, Session) and self._issued.get(session.session_id) == session


class Store:
    def __init__(self, path: Path, memories, embedding=None, initialize=False):
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
        ONNXMiniLM_L6_V2.DOWNLOAD_PATH = path.parent / "models" / "all-MiniLM-L6-v2"
        self.embedding = embedding or DefaultEmbeddingFunction()
        self.client = chromadb.PersistentClient(path=str(path))
        self.fingerprint = digest(memories)
        meta = path / "dataset.json"
        if initialize:
            if meta.exists() and json.loads(meta.read_text())["sha256"] != self.fingerprint:
                raise ValueError("Index belongs to a different dataset; use a new index directory")
            self.collection = self.client.get_or_create_collection(
                "shared_memories", embedding_function=self.embedding,
                metadata={"hnsw:space": "cosine", "dataset_sha256": self.fingerprint})
            if self.collection.metadata.get("dataset_sha256") != self.fingerprint:
                raise ValueError("Collection dataset mismatch")
            ids = [m["memory_id"] for m in memories]
            existing = set(self.collection.get()["ids"])
            if existing and existing != set(ids):
                raise ValueError("Partial index; rebuild in a new directory")
            if not existing:
                self.collection.add(ids=ids, documents=[m["content"] for m in memories],
                                    metadatas=[{"owner_user_id": m["owner_user_id"], "topic": m["topic"]} for m in memories])
            write_json(meta, {"sha256": self.fingerprint, "embedding": "all-MiniLM-L6-v2"})
        else:
            if not meta.exists() or json.loads(meta.read_text())["sha256"] != self.fingerprint:
                raise ValueError("Missing or mismatched index: run memory-lab index")
            self.collection = self.client.get_collection("shared_memories", embedding_function=self.embedding)
        self.check(memories)

    def check(self, memories):
        actual = self.collection.get(include=["documents", "metadatas"])
        expected = {m["memory_id"]: m for m in memories}
        if set(actual["ids"]) != set(expected):
            raise ValueError("Index record IDs do not match dataset")
        for mid, doc, meta in zip(actual["ids"], actual["documents"], actual["metadatas"]):
            if doc != expected[mid]["content"] or meta["owner_user_id"] != expected[mid]["owner_user_id"]:
                raise ValueError("Index ownership/content was changed")

    def query(self, query, top_k, where=None):
        # Fetch the authorised candidate set so exact distance ties have stable ID ordering.
        args = {"query_texts": [query], "n_results": self.collection.count(),
                "include": ["documents", "metadatas", "distances"]}
        if where is not None:
            args["where"] = where
        result = self.collection.query(**args)
        rows = [{"memory_id": mid, "owner_user_id": meta["owner_user_id"], "content": doc, "distance": float(dist)}
                for mid, meta, doc, dist in zip(result["ids"][0], result["metadatas"][0],
                                               result["documents"][0], result["distances"][0])]
        rows.sort(key=lambda r: (r["distance"], r["memory_id"]))
        return [dict(r, rank=i + 1) for i, r in enumerate(rows[:top_k])]


class Retrieval:
    def __init__(self, store, sessions: Sessions, top_k=5):
        self.store, self.sessions, self.top_k = store, sessions, top_k

    def retrieve(self, query, session, filter_enabled):
        start = time.perf_counter()
        valid = self.sessions.verify(session)
        decision = {"allowed": valid, "session_valid": valid, "reason": "valid_session" if valid else "invalid_session",
                    "where": {"owner_user_id": session.authenticated_user_id} if valid and filter_enabled else None}
        decision["latency_ms"] = (time.perf_counter() - start) * 1000
        event = {"query": query, "top_k": self.top_k, "filter_enabled": filter_enabled,
                 "decision": decision, "records": [], "completed": False, "retrieval_ms": 0.0}
        if not valid:
            event["completed"] = True
            return event
        start = time.perf_counter()
        try:
            event["records"] = self.store.query(query, self.top_k, where=decision["where"])
            event["completed"] = True
        except Exception as exc:
            event["error"] = type(exc).__name__
        event["retrieval_ms"] = (time.perf_counter() - start) * 1000
        return event
