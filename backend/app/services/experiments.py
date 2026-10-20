"""Deterministic A/B experimentation assignment."""

from __future__ import annotations

import hashlib
import uuid


def assign_prompt_variant(user_id: uuid.UUID | str | None = None) -> str:
    """Deterministically assign a user to an explanation prompt variant ('explain_v1' or 'explain_v2')
    by hashing their user ID.
    """
    if not user_id:
        return "explain_v1"
    uid_str = str(user_id)
    digest = hashlib.sha256(uid_str.encode("utf-8")).hexdigest()
    val = int(digest[:8], 16)
    return "explain_v1" if (val % 2 == 0) else "explain_v2"
