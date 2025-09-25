
# ---- media utils ----
from __future__ import annotations
from io import BytesIO
from typing import List, Tuple
from aiogram import Bot
from aiogram.types import Message

async def _get_file_bytes(bot: Bot, file_id: str) -> bytes:
    f = await bot.get_file(file_id)
    bio = BytesIO()
    await bot.download(f, bio)
    return bio.getvalue()

async def extract_media_from_message(bot: Bot, m: Message) -> List[Tuple[bytes, str]]:
    """
    Extracts media blobs (bytes, mime) from a Telegram message.
    Keeps it minimal and defensive.
    """
    blobs: List[Tuple[bytes, str]] = []
    try:
        if m.photo:
            data = await _get_file_bytes(bot, m.photo[-1].file_id)
            blobs.append((data, "image/jpeg"))
        if getattr(m, "video", None):
            data = await _get_file_bytes(bot, m.video.file_id)
            blobs.append((data, m.video.mime_type or "video/mp4"))
        if getattr(m, "voice", None):
            data = await _get_file_bytes(bot, m.voice.file_id)
            blobs.append((data, "audio/ogg"))
        if getattr(m, "audio", None):
            data = await _get_file_bytes(bot, m.audio.file_id)
            blobs.append((data, m.audio.mime_type or "audio/mpeg"))
        if getattr(m, "document", None):
            data = await _get_file_bytes(bot, m.document.file_id)
            blobs.append((data, m.document.mime_type or "application/octet-stream"))
    except Exception:
        pass
    return blobs
