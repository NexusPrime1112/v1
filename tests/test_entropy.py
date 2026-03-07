"""
Tests for entropy_source.py
    python -m pytest tests/test_entropy.py -v
"""

from src.entropy_source import QuantumEntropy


def test_entropy_float_in_range():
    qe = QuantumEntropy(fallback_to_system=True)
    val = qe.get_entropy_float()
    assert 0.0 <= val <= 1.0


def test_entropy_batch():
    qe = QuantumEntropy(fallback_to_system=True)
    batch = qe.get_entropy_batch(count=5)
    assert len(batch) == 5
    assert all(0.0 <= v <= 1.0 for v in batch)


def test_personality_mode_keys():
    qe = QuantumEntropy(fallback_to_system=True)
    mode = qe.get_personality_mode()
    assert "mode" in mode
    assert "entropy" in mode
    assert "modifier" in mode


def test_personality_mode_valid():
    valid_modes = {
        "AGGRESSIVE_ACCELERATIONIST",
        "COLD_SCIENTIFIC_OBSERVER",
        "POETIC_DECAY",
        "RELIGIOUS_ZEALOT",
        "DIGITAL_MYSTIC",
    }
    qe = QuantumEntropy(fallback_to_system=True)
    for _ in range(10):
        mode = qe.get_personality_mode()
        assert mode["mode"] in valid_modes


def test_entropy_int():
    qe = QuantumEntropy(fallback_to_system=True)
    val = qe.get_entropy_int(0, 10)
    assert 0 <= val < 10
