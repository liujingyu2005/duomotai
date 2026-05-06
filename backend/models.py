from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatSession:
    chat_id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict[str, Any]] = field(default_factory=list)
