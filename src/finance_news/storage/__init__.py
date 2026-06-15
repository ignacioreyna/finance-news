"""Local filesystem storage for raw payloads and normalized SourceItems.

MVP scope: single-process; no concurrent-write handling.
"""

from __future__ import annotations

from finance_news.storage.local import LocalStorage

__all__ = ["LocalStorage"]