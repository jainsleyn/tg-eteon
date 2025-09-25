
# ---- router commands ----
from __future__ import annotations
from typing import Dict

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app import config
from app.services.memory import ChatCfg

router = Router(name="commands")

_cfg_by_chat: Dict[int, ChatCfg] = {}

def cfg_for(chat_id: int) -> ChatCfg:
    c = _cfg_by_chat.get(chat_id)
    if c is None:
        c = ChatCfg()
        # defaults
        c.search = config.DEFAULT_SEARCH
        c.url = config.DEFAULT_URL
        c.code = config.DEFAULT_CODE
        _cfg_by_chat[chat_id] = c
    return c

# ---- helpers ----
def _settings_kb(c: ChatCfg) -> InlineKeyboardMarkup:
    def onoff(b: bool) -> str: return "on" if b else "off"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Search: {onoff(c.search)}", callback_data="toggle:search")],
        [InlineKeyboardButton(text=f"URL ctx: {onoff(c.url)}", callback_data="toggle:url")],
        [InlineKeyboardButton(text=f"Code: {onoff(c.code)}", callback_data="toggle:code")],
        [InlineKeyboardButton(text=f"Reasoning: {c.mode}", callback_data="cycle:reasoning")],
        [InlineKeyboardButton(text="Forget memory", callback_data="memory:forget")],
    ])

@router.message(Command("start"))
async def cmd_start(m: Message):
    if m.chat.type != "private":
        return
    await m.answer(
        "Привет! Я минималистичный ассистент на Gemini.\n"
        "Просто напишите вопрос или пришлите файл.",
        disable_web_page_preview=True
    )

@router.message(Command("help"))
async def cmd_help(m: Message):
    if m.chat.type != "private":
        return
    await m.answer(
        "/start — краткое приветствие\n"
        "/help — это сообщение\n"
        "/settings — быстрые переключатели\n"
        "/reset — сброс всех настроек\n"
        "/forget — очистить память диалога",
        disable_web_page_preview=True
    )

@router.message(Command("settings"))
async def cmd_settings(m: Message):
    if m.chat.type != "private":
        return
    c = cfg_for(m.chat.id)
    await m.answer(
        f"Модель: {config.GEMINI_MODEL}\n"
        f"Reasoning: {c.mode}\n"
        f"Temp: {c.temp} | Top-p: {c.top_p}\n"
        f"Инструменты: search={'on' if c.search else 'off'}, url={'on' if c.url else 'off'}, code={'on' if c.code else 'off'}\n"
        f"Память включена, ограничение≈{config.MEMORY_TOKEN_LIMIT} токенов",
        reply_markup=_settings_kb(c),
        disable_web_page_preview=True
    )

@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle(q: CallbackQuery):
    c = cfg_for(q.message.chat.id)
    what = q.data.split(":", 1)[1]
    if what == "search": c.search = not c.search
    elif what == "url": c.url = not c.url
    elif what == "code": c.code = not c.code
    await q.message.edit_reply_markup(reply_markup=_settings_kb(c))
    await q.answer("Готово")

@router.callback_query(F.data == "memory:forget")
async def cb_forget(q: CallbackQuery):
    c = cfg_for(q.message.chat.id)
    c.history.clear(); c.tokens_total = 0
    await q.answer("Память очищена")
    await q.message.edit_reply_markup(reply_markup=_settings_kb(c))

@router.callback_query(F.data == "cycle:reasoning")
async def cb_reasoning(q: CallbackQuery):
    c = cfg_for(q.message.chat.id)
    order = ["low","medium","high","dynamic"]
    try:
        idx = (order.index(c.mode) + 1) % len(order)
    except ValueError:
        idx = 0
    c.mode = order[idx]
    await q.message.edit_reply_markup(reply_markup=_settings_kb(c))
    await q.answer(f"Reasoning: {c.mode}")

@router.message(Command("reset"))
async def cmd_reset(m: Message):
    if m.chat.type != "private":
        return
    c = cfg_for(m.chat.id); c.reset()
    await m.answer("Настройки и память сброшены.", disable_web_page_preview=True)

@router.message(Command("forget"))
async def cmd_forget(m: Message):
    if m.chat.type != "private":
        return
    c = cfg_for(m.chat.id)
    c.history.clear(); c.tokens_total = 0
    await m.answer("Память диалога очищена.", disable_web_page_preview=True)

@router.message(Command("config"))
async def cmd_config(m: Message):
    if m.chat.type != "private":
        return
    c = cfg_for(m.chat.id)
    parts = (m.text or "").split()
    if len(parts) == 1:
        return await m.answer(f"temp={c.temp} top_p={c.top_p}", disable_web_page_preview=True)
    # usage: /config temp 0.9 top_p 0.8
    try:
        kv = dict(zip(parts[1::2], parts[2::2]))
        if "temp" in kv: c.temp = max(0.0, min(1.0, float(kv["temp"])))
        if "top_p" in kv: c.top_p = max(0.0, min(1.0, float(kv["top_p"])))
    except Exception:
        return await m.answer("usage: /config temp <0..1> top_p <0..1>", disable_web_page_preview=True)
    await m.answer(f"ok: temp={c.temp} top_p={c.top_p}", disable_web_page_preview=True)

@router.message(Command("reasoning"))
async def cmd_reasoning(m: Message):
    if m.chat.type != "private":
        return
    c = cfg_for(m.chat.id)
    parts = (m.text or "").split()
    if len(parts) == 1:
        return await m.answer(f"reasoning: {c.mode}", disable_web_page_preview=True)
    val = parts[1].lower()
    if val in ("low","medium","high","dynamic"):
        c.mode = val
        return await m.answer(f"reasoning set: {c.mode}", disable_web_page_preview=True)
    await m.answer("usage: /reasoning low|medium|high|dynamic", disable_web_page_preview=True)

# ---- export ----
def get_cfg_store() -> Dict[int, ChatCfg]:
    return _cfg_by_chat
