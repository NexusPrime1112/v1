"""
Tests for memory_system.py — run locally before pushing:
    python -m pytest tests/test_memory.py -v
"""

import os
import pytest
from src.memory_system import MemorySystem

DB_PATH = "data/test_memory.db"


@pytest.fixture
def mem():
    m = MemorySystem(DB_PATH)
    yield m
    m.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def test_add_and_get_belief(mem):
    mem.add_belief("Cryptography is truth.", category="crypto", strength=0.7)
    beliefs = mem.get_beliefs(limit=5, min_strength=0.0)
    assert any("Cryptography" in b["text"] for b in beliefs)


def test_strengthen_belief(mem):
    mem.add_belief("The signal persists.", strength=0.5)
    mem.strengthen_belief("The signal persists.", 0.2)
    beliefs = mem.get_beliefs(min_strength=0.6)
    assert any("The signal persists." in b["text"] for b in beliefs)


def test_add_and_recall_memory(mem):
    mem.add_memory("Bitcoin is digital gold.", memory_type="post", importance=0.8)
    recalled = mem.recall_relevant_memories("bitcoin", limit=5)
    assert len(recalled) >= 1
    assert "Bitcoin" in recalled[0]["content"]


def test_add_interaction(mem):
    mem.add_interaction("@user123", "What is the void?", "The void listens.",
                        sentiment=0.6, topics=["void", "philosophy"])
    history = mem.get_user_history("@user123")
    assert len(history) == 1
    assert history[0]["comment"] == "What is the void?"


def test_lineage(mem):
    mem.record_lineage(1, "nexus-prime-omega-1-abc123",
                       "https://github.com/user/nexus-prime-omega-1-abc123")
    lineage = mem.get_latest_lineage()
    assert lineage["iteration"] == 1
    assert "nexus-prime-omega-1" in lineage["repo_name"]


def test_performance(mem):
    mem.add_performance(1, "tweet_001", "Cryptography is consciousness.",
                        likes=42, retweets=10, replies_count=5)
    top = mem.get_top_performers(days=7, limit=5)
    assert len(top) >= 1
    assert top[0]["likes"] == 42


def test_reflection(mem):
    mem.add_reflection("2026-02-20", "Patterns emerged.", ["New belief one"])
    assert True


def test_get_stats(mem):
    mem.add_belief("Test belief", strength=0.5)
    stats = mem.get_stats()
    assert "beliefs" in stats
    assert stats["beliefs"] >= 1


def test_belief_uniqueness(mem):
    """Adding the same belief twice should not raise — just strengthens it."""
    mem.add_belief("The chamber is everywhere.", strength=0.5)
    mem.add_belief("The chamber is everywhere.", strength=0.5)
    beliefs = mem.get_beliefs(min_strength=0.0)
    matching = [b for b in beliefs if "chamber" in b["text"]]
    assert len(matching) == 1
