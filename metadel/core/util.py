"""Tiny shared helpers."""

from __future__ import annotations


def truncate(value: object, limit: int = 80) -> str:
    """One-line, length-capped string for showing a residual value to the user."""
    s = "" if value is None else str(value)
    s = s.replace("\r", " ").replace("\n", " ").strip()
    if len(s) > limit:
        s = s[: limit - 1] + "…"
    return s
