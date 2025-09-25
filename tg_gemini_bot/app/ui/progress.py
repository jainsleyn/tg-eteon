
# ---- progress ui ----
import asyncio
from typing import Optional
from aiogram import Bot
from aiogram.enums import ChatAction

from app.config import PROGRESS_EDIT_INTERVAL, TYPING_INTERVAL

class ProgressUI:
    """
    Single editable message + background typing sender.
    Use as async context manager:
        async with ProgressUI(bot, chat_id, reply_to) as ui:
            await ui.set_text("Thinking…")
            ...
    """
    SPINNER = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, bot: Bot, chat_id: int, reply_to_message_id: Optional[int] = None) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.reply_to_message_id = reply_to_message_id
        self.msg_id: Optional[int] = None
        self._stop = asyncio.Event()
        self._typing_task: Optional[asyncio.Task] = None
        self._spinner_task: Optional[asyncio.Task] = None
        self._spinner_i = 0
        self._last_edit_ts = 0.0

    async def __aenter__(self) -> "ProgressUI":
        m = await self.bot.send_message(
            self.chat_id,
            "Thinking ⠋",
            reply_to_message_id=self.reply_to_message_id,
            disable_web_page_preview=True
        )
        self.msg_id = m.message_id
        self._typing_task = asyncio.create_task(self._typing_loop())
        self._spinner_task = asyncio.create_task(self._spinner_loop())
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._stop.set()
        for t in (self._typing_task, self._spinner_task):
            if t:
                t.cancel()
        # If something remains, try to delete spinner
        try:
            if self.msg_id:
                await self.bot.delete_message(self.chat_id, self.msg_id)
        except Exception:
            pass

    async def _typing_loop(self):
        try:
            while not self._stop.is_set():
                await self.bot.send_chat_action(chat_id=self.chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(TYPING_INTERVAL)
        except Exception:
            return

    async def _spinner_loop(self):
        try:
            while not self._stop.is_set():
                await asyncio.sleep(PROGRESS_EDIT_INTERVAL)
                self._spinner_i += 1
                await self._safe_edit(f"Thinking {self.SPINNER[self._spinner_i % len(self.SPINNER)]}")
        except Exception:
            return

    async def _safe_edit(self, text: str):
        if not self.msg_id:
            return
        try:
            await self.bot.edit_message_text(
                text=text,
                chat_id=self.chat_id,
                message_id=self.msg_id,
                disable_web_page_preview=True
            )
        except Exception:
            # ignore edit rate/ordering errors
            pass

    async def set_text(self, text: str):
        await self._safe_edit(text)
