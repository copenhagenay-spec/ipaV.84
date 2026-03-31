"""
VERA license gating.

Currently backed by a plain config flag ("premium": true).
Will be replaced by cryptographic key validation before commercial launch.
"""

from __future__ import annotations


def is_premium() -> bool:
    """Return True if this install is running in premium mode."""
    try:
        from config import load_config
        return bool(load_config().get("premium", False))
    except Exception:
        return False
