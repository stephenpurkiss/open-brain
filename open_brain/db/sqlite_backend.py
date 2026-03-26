"""SQLite backend for Open Brain -- zero external dependencies beyond Python stdlib + numpy."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta


class SQLiteBackend:
    """Store and search thoughts using SQLite with in-memory vector similarity."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.expanduser("~/.open-brain/brain.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS thoughts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                scope TEXT DEFAULT 'private',
                source TEXT,
                embedding TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.conn.commit()

    def capture(self, content, category="general", scope="private", source=None, embedding=None):
        thought_id = str(uuid.uuid4())
        emb_json = json.dumps(embedding) if embedding else None
        self.conn.execute(
            "INSERT INTO thoughts (id, content, category, scope, source, embedding) VALUES (?, ?, ?, ?, ?, ?)",
            (thought_id, content, category, scope, source, emb_json)
        )
        self.conn.commit()
        row = self.conn.execute("SELECT created_at FROM thoughts WHERE id = ?", (thought_id,)).fetchone()
        return {"id": thought_id, "created_at": row["created_at"], "status": "captured"}

    def search(self, query_embedding, limit=10, category=None):
        import numpy as np

        sql = "SELECT id, content, category, source, created_at, embedding FROM thoughts WHERE embedding IS NOT NULL"
        params = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        rows = self.conn.execute(sql, params).fetchall()

        if not rows:
            return self._text_search("", limit, category)

        query_vec = np.array(query_embedding, dtype=np.float32)
        results = []
        for row in rows:
            emb = np.array(json.loads(row["embedding"]), dtype=np.float32)
            similarity = float(np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8))
            results.append({
                "id": row["id"],
                "content": row["content"],
                "category": row["category"],
                "source": row["source"],
                "created_at": row["created_at"],
                "similarity": round(similarity, 4),
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _text_search(self, query, limit, category):
        sql = "SELECT id, content, category, source, created_at FROM thoughts"
        params = []
        conditions = []
        if query:
            conditions.append("content LIKE ?")
            params.append(f"%{query}%")
        if category:
            conditions.append("category = ?")
            params.append(category)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def browse_recent(self, hours=24, category=None, limit=20):
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        sql = "SELECT id, content, category, source, created_at FROM thoughts WHERE created_at > ?"
        params = [cutoff]
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def stats(self):
        total = self.conn.execute("SELECT count(*) FROM thoughts").fetchone()[0]
        cats = self.conn.execute("SELECT category, count(*) as cnt FROM thoughts GROUP BY category ORDER BY cnt DESC").fetchall()
        categories = {row["category"]: row["cnt"] for row in cats}
        dates = self.conn.execute("SELECT min(created_at), max(created_at) FROM thoughts").fetchone()
        embedded = self.conn.execute("SELECT count(*) FROM thoughts WHERE embedding IS NOT NULL").fetchone()[0]
        return {
            "total_thoughts": total,
            "embedded": embedded,
            "categories": categories,
            "earliest": dates[0],
            "latest": dates[1],
        }
