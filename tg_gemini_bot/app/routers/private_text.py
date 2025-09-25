
# ---- router private ----
from __future__ import annotations
import asyncio
from typing import List, Tuple

from aiogram import Router, F
from aiogram.types import Message

from app import config
from app.ui.progress import ProgressUI
from app.ui.chunking import chunk_text
from app.utils.media import extract_media_from_message
from app.utils.guards import ChatGate
from app.services import gemini
from app.services.memory import ChatCfg, memory_append
from app.routers.commands import cfg_for

router = Router(name="private")
_gate = ChatGate()

def _is_empty(s: str) -> bool:
    return not s or not s.strip()

@router.message(F.chat.type == "private")
async def handle_private_message(m: Message):
    # ---- per-chat lock ----
    async with (await _gate.enter(m.chat.id)):
        try:
            prompt = (m.text or m.caption or "").strip()
            blobs: List[Tuple[bytes, str]] = await extract_media_from_message(m.bot, m)
            c: ChatCfg = cfg_for(m.chat.id)

            if _is_empty(prompt) and not blobs:
                # silently ignore empty
                return

            # ---- progress ui ----
            async with ProgressUI(m.bot, m.chat.id, reply_to_message_id=m.message_id) as ui:
                # Prefer streaming if enabled
                if config.ENABLE_STREAMING:
                    if (m.text or '').startswith('/'):
                        return
                    acc = ""
                    full = ""
                    async for delta in gemini.stream_generate(prompt, c, blobs if blobs else None):
                        acc += delta
                        full += delta
                        # Edit progress until first chunk is stable
                        if len(acc) < config.TELEGRAM_CHUNK_SIZE:
                            await ui.set_text(acc if acc else "Thinking…")
                        else:
                            # Send first full chunk, then continue via messages
                            pieces = chunk_text(acc)
                            await m.answer(pieces[0], disable_web_page_preview=True)
                            for p in pieces[1:]:
                                await m.answer(p, disable_web_page_preview=True)
                            acc = ""
                    # Flush tail if any
                    if acc:
                        for p in chunk_text(acc):
                            await m.answer(p, disable_web_page_preview=True)
                else:
                    # Non-streaming path
                    if (m.text or '').startswith('/'):
                        return
                    if blobs:
                        reply = await gemini.generate_multimodal(prompt or "Analyze input.", c, blobs)
                    else:
                        reply = await gemini.generate_text(prompt, c)
                    for p in chunk_text(reply):
                        await m.answer(p, disable_web_page_preview=True)
                    full = reply

            # ---- memory window ----
            memory_append(c, prompt or "[media]", full if 'full' in locals() else "")

        except asyncio.CancelledError:
            # Another request came in; just stop silently
            return
        except Exception:
            # Minimalism: no verbose error to user
            await m.answer("Что‑то пошло не так. Попробуйте ещё раз.", disable_web_page_preview=True)
