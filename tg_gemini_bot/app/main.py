
# ---- entrypoint / polling ----
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ChatMemberUpdated

from app import config
from app.routers import commands, private_text

def _build_dp() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(commands.router)
    dp.include_router(private_text.router)

    # ---- hard private-only policy ----
    sys_router = Router(name="system")

    @sys_router.my_chat_member()
    async def on_my_chat_member(ev: ChatMemberUpdated):
        # If added to any non-private chat, leave immediately
        if ev.chat.type in ("group", "supergroup", "channel"):
            try:
                await ev.bot.leave_chat(ev.chat.id)
            except Exception:
                pass

    dp.include_router(sys_router)
    return dp

async def main():
    config.ensure_env()
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=None))
    dp = _build_dp()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
