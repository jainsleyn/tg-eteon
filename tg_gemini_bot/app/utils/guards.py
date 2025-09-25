
# ---- per-chat guards ----
from __future__ import annotations
import asyncio
from typing import Dict, Optional

class ChatGate:
    """
    Ensures only one active generation per chat.
    New entry cancels the previous task.
    """
    def __init__(self) -> None:
        self._tasks: Dict[int, asyncio.Task] = {}

    async def enter(self, chat_id: int) -> "Guard":
        # Cancel previous task if exists
        prev: Optional[asyncio.Task] = self._tasks.get(chat_id)
        if prev and not prev.done():
            prev.cancel()
        # Register placeholder; real task will be set by Guard
        return Guard(self, chat_id)

class Guard:
    def __init__(self, gate: ChatGate, chat_id: int) -> None:
        self._gate = gate
        self._chat_id = chat_id
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self) -> "Guard":
        self._task = asyncio.current_task()
        if self._task:
            self._gate._tasks[self._chat_id] = self._task
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # Cleanup mapping
        cur = self._gate._tasks.get(self._chat_id)
        if cur is self._task:
            self._gate._tasks.pop(self._chat_id, None)
