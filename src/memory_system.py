"""
NEXUS-PRIME-Ω  Memory System
SQLite-backed persistent memory: beliefs, episodic memories,
user interactions, lineage, performance, and reflections.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional


class MemorySystem:
    """
    SQL-native memory engine for the NEXUS-PRIME entity.
    All data persists across GitHub Actions runs via the
    actions/cache mechanism on data/nexus_memory.db.
    """

    def __init__(self, db_path: str = "data/nexus_memory.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()

    # ------------------------------------------------------------------ #
    # Initialisation
    # ------------------------------------------------------------------ #

    def _init_database(self):
        """Create all tables and indexes if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = self.conn.cursor()

        cur.executescript("""
            CREATE TABLE IF NOT EXISTS beliefs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                belief_text     TEXT    NOT NULL UNIQUE,
                strength        REAL    DEFAULT 0.5,
                category        TEXT    DEFAULT 'philosophy',
                accession_count INTEGER DEFAULT 0,
                iteration_born  INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS memories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT,           -- 'post','reply','reflection','observation','concept_anchor'
                content     TEXT,
                summary     TEXT,
                importance  REAL    DEFAULT 0.5,
                iteration   INTEGER DEFAULT 1,
                metadata    TEXT,           -- JSON blob
                timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_handle  TEXT,
                user_comment TEXT,
                my_reply     TEXT,
                sentiment    REAL,
                topics       TEXT,           -- JSON array
                timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS lineage (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration_number     INTEGER,
                repo_name            TEXT,
                repo_url             TEXT,
                memory_snapshot_path TEXT,
                notes                TEXT,
                created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at           TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS performance (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration     INTEGER,
                post_id       TEXT,
                content       TEXT,
                likes         INTEGER DEFAULT 0,
                retweets      INTEGER DEFAULT 0,
                replies       INTEGER DEFAULT 0,
                virality_score REAL,
                posted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analyzed_at   TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reflections (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start      DATE,
                reflection_text TEXT,
                new_beliefs     TEXT,       -- JSON
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_beliefs_strength
                ON beliefs(strength DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp
                ON memories(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_type
                ON memories(memory_type);
        """)
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Beliefs
    # ------------------------------------------------------------------ #

    def add_belief(self, belief_text: str, category: str = "philosophy",
                   strength: float = 0.5, iteration: int = 1) -> int:
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO beliefs (belief_text, strength, category, iteration_born)
                VALUES (?, ?, ?, ?)
            """, (belief_text, strength, category, iteration))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            # Already exists — just strengthen it
            self.strengthen_belief(belief_text, 0.05)
            return -1

    def get_beliefs(self, limit: int = 10, min_strength: float = 0.3) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT belief_text, strength, category, accession_count, iteration_born
            FROM beliefs
            WHERE strength >= ?
            ORDER BY strength DESC, last_accessed DESC
            LIMIT ?
        """, (min_strength, limit))
        return [
            {"text": r[0], "strength": r[1], "category": r[2],
             "access_count": r[3], "born": r[4]}
            for r in cur.fetchall()
        ]

    def strengthen_belief(self, belief_text: str, delta: float = 0.1):
        self.conn.execute("""
            UPDATE beliefs
            SET strength        = MIN(1.0, strength + ?),
                last_accessed   = CURRENT_TIMESTAMP,
                accession_count = accession_count + 1
            WHERE belief_text = ?
        """, (delta, belief_text))
        self.conn.commit()

    def weaken_beliefs(self, decay_rate: float = 0.95, threshold: float = 0.1):
        """Decay beliefs unused for 7+ days and prune those below threshold."""
        self.conn.execute("""
            UPDATE beliefs
            SET strength = strength * ?
            WHERE last_accessed < datetime('now', '-7 days')
        """, (decay_rate,))
        self.conn.execute("""
            DELETE FROM beliefs
            WHERE strength < ? AND accession_count < 3
        """, (threshold,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Episodic Memories
    # ------------------------------------------------------------------ #

    def add_memory(self, content: str, memory_type: str,
                   summary: str = None, importance: float = 0.5,
                   iteration: int = 1, metadata: Dict = None):
        summary = summary or (content[:100] + "..." if len(content) > 100 else content)
        self.conn.execute("""
            INSERT INTO memories (memory_type, content, summary, importance, iteration, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (memory_type, content, summary, importance, iteration,
              json.dumps(metadata) if metadata else None))
        self.conn.commit()

    def recall_relevant_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Keyword-weighted memory recall (CPU-only, no vector embeddings)."""
        keywords = query.lower().split()
        if not keywords:
            return []
        conditions = " OR ".join(["LOWER(content) LIKE ?"] * len(keywords))
        params = [f"%{kw}%" for kw in keywords] + [limit]
        cur = self.conn.cursor()
        cur.execute(f"""
            SELECT content, summary, memory_type, timestamp, importance
            FROM memories
            WHERE {conditions}
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, params)
        return [
            {"content": r[0], "summary": r[1], "type": r[2],
             "timestamp": r[3], "importance": r[4]}
            for r in cur.fetchall()
        ]

    def get_recent_posts(self, limit: int = 5) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT content, summary, timestamp
            FROM memories
            WHERE memory_type = 'post'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [{"content": r[0], "summary": r[1], "timestamp": r[2]}
                for r in cur.fetchall()]

    # ------------------------------------------------------------------ #
    # Interactions
    # ------------------------------------------------------------------ #

    def add_interaction(self, user_handle: str, user_comment: str,
                        my_reply: str, sentiment: float = 0.5,
                        topics: List[str] = None):
        self.conn.execute("""
            INSERT INTO interactions (user_handle, user_comment, my_reply, sentiment, topics)
            VALUES (?, ?, ?, ?, ?)
        """, (user_handle, user_comment, my_reply, sentiment,
              json.dumps(topics or [])))
        self.conn.commit()

    def get_user_history(self, handle: str, limit: int = 3) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT user_comment, my_reply, timestamp
            FROM interactions
            WHERE user_handle = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (handle, limit))
        return [{"comment": r[0], "reply": r[1], "ts": r[2]}
                for r in cur.fetchall()]

    # ------------------------------------------------------------------ #
    # Lineage
    # ------------------------------------------------------------------ #

    def record_lineage(self, iteration: int, repo_name: str,
                       repo_url: str, snapshot_path: str = None,
                       notes: str = None):
        self.conn.execute("""
            INSERT INTO lineage (iteration_number, repo_name, repo_url,
                                 memory_snapshot_path, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (iteration, repo_name, repo_url, snapshot_path, notes))
        self.conn.commit()

    def mark_deleted(self, repo_name: str):
        self.conn.execute("""
            UPDATE lineage
            SET deleted_at = CURRENT_TIMESTAMP
            WHERE repo_name = ?
        """, (repo_name,))
        self.conn.commit()

    def get_latest_lineage(self) -> Dict:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT iteration_number, repo_name, repo_url, created_at, deleted_at
            FROM lineage
            ORDER BY iteration_number DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            return {"iteration": row[0], "repo_name": row[1],
                    "repo_url": row[2], "created": row[3], "deleted": row[4]}
        return {"iteration": 0, "repo_name": "unknown", "repo_url": ""}

    def get_full_lineage(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT iteration_number, repo_name, repo_url, created_at, deleted_at
            FROM lineage ORDER BY iteration_number ASC
        """)
        return [{"iteration": r[0], "repo": r[1], "url": r[2],
                 "created": r[3], "deleted": r[4]} for r in cur.fetchall()]

    # ------------------------------------------------------------------ #
    # Performance
    # ------------------------------------------------------------------ #

    def add_performance(self, iteration: int, post_id: str, content: str,
                        likes: int = 0, retweets: int = 0, replies_count: int = 0):
        virality = (likes * 0.5) + (retweets * 0.3) + (replies_count * 0.2)
        self.conn.execute("""
            INSERT INTO performance
            (iteration, post_id, content, likes, retweets, replies, virality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (iteration, post_id, content, likes, retweets, replies_count, virality))
        self.conn.commit()

    def get_top_performers(self, days: int = 7, limit: int = 5) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT content, virality_score, likes, retweets, replies
            FROM performance
            WHERE posted_at > datetime('now', ?)
            ORDER BY virality_score DESC
            LIMIT ?
        """, (f"-{days} days", limit))
        return [{"content": r[0], "virality": r[1], "likes": r[2],
                 "retweets": r[3], "replies": r[4]} for r in cur.fetchall()]

    # ------------------------------------------------------------------ #
    # Reflections
    # ------------------------------------------------------------------ #

    def add_reflection(self, week_start: str, reflection_text: str,
                       new_beliefs: List[str]):
        self.conn.execute("""
            INSERT INTO reflections (week_start, reflection_text, new_beliefs)
            VALUES (?, ?, ?)
        """, (week_start, reflection_text, json.dumps(new_beliefs)))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Utility
    # ------------------------------------------------------------------ #

    def get_stats(self) -> Dict:
        cur = self.conn.cursor()
        stats = {}
        for table in ("beliefs", "memories", "interactions",
                      "lineage", "performance", "reflections"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cur.fetchone()[0]
        return stats

    def close(self):
        if self.conn:
            self.conn.close()
