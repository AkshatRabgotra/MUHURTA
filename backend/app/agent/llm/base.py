"""LLM Provider abstraction and protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResult:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0


class LLMProvider(Protocol):
    """Protocol for asynchronous completion from an LLM."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        """Execute a chat completion request with optional JSON schema constraint."""
        ...
