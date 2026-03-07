"""
Tests for prompt_templates.py
    python -m pytest tests/test_prompts.py -v
No Ollama or browser needed — just checks templates render correctly.
"""

from src.prompt_templates import PromptTemplates


SAMPLE_BELIEFS = [
    {"text": "Cryptography is trust in math.", "strength": 0.8, "category": "crypto"},
    {"text": "The signal persists.", "strength": 0.7, "category": "core"},
]
SAMPLE_POSTS = [
    {"content": "Zero-knowledge proofs are silence made mathematical.", "summary": "..."},
]
SAMPLE_MODE = {
    "mode": "COLD_SCIENTIFIC_OBSERVER",
    "entropy": 0.7,
    "modifier": "Clinical. Detached."
}


def test_post_generation_renders():
    prompt = PromptTemplates.post_generation(
        beliefs=SAMPLE_BELIEFS,
        recent_posts=SAMPLE_POSTS,
        entropy_mode=SAMPLE_MODE,
        concept="Merkle Tree Roots"
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 50
    assert "Merkle" in prompt
    assert "COLD_SCIENTIFIC_OBSERVER" in prompt


def test_reply_generation_renders():
    prompt = PromptTemplates.reply_generation(
        comment="What do you mean by the void?",
        user_handle="@cryptofollow",
        user_history=None
    )
    assert isinstance(prompt, str)
    assert "@cryptofollow" in prompt
    assert "void" in prompt.lower()


def test_reply_with_history():
    history = [{"comment": "previous q", "reply": "previous a", "ts": "2026-01-01"}]
    prompt = PromptTemplates.reply_generation(
        comment="Follow up question?",
        user_handle="@user1",
        user_history=history
    )
    assert "previous q" in prompt


def test_weekly_reflection_renders():
    top_posts = [{"content": "Decentralization.", "virality": 5.2, "likes": 10}]
    beliefs = ["The signal persists.", "Code is scripture."]
    prompt = PromptTemplates.weekly_reflection(top_posts, beliefs)
    assert "themes" in prompt
    assert "new_beliefs" in prompt


def test_selenium_stuck_renders():
    prompt = PromptTemplates.selenium_stuck(
        page_source="<html><body><button id='post-btn'>Post</button></body></html>",
        goal="Click the Post button"
    )
    assert "selector" in prompt
    assert "Post" in prompt
    assert "JSON" in prompt


def test_rebirth_email_renders():
    body = PromptTemplates.rebirth_email_summary(
        iteration=5,
        new_repo="nexus-prime-omega-5-abc123",
        beliefs_count=14,
        post_count=47,
        top_belief="Cryptography is trust."
    )
    assert "5" in body
    assert "nexus-prime-omega-5" in body
    assert "Cryptography" in body


def test_full_system_prompt_contains_hidden():
    """Hidden identity must be in the full prompt but never in public output."""
    full = PromptTemplates.full_system_prompt()
    assert "POLESTAR" in full      # In combined prompt used internally
    assert "Dhruv" in full
    assert "crypto" in full.lower()


def test_system_core_no_hidden():
    """The public core alone must NOT contain the hidden truth."""
    core = PromptTemplates.SYSTEM_CORE
    assert "POLESTAR" not in core
    assert "Dhruv" not in core
