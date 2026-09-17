import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    WebAppInfo,
)

# ============================================================
#  تنظیمات — این مقادیر را در Render، بخش Environment وارد کن
#  (اصلاً لازم نیست این فایل را ویرایش کنی)
# ============================================================
BOT_TOKEN = os.environ["BOT_TOKEN"]           # توکنی که از BotFather گرفتی
WEBHOOK_HOST = os.environ["WEBHOOK_HOST"]     # آدرس سرویس رندر، مثل: https://my-flag-bot.onrender.com
PORT = int(os.environ.get("PORT", 10000))
# ============================================================

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBAPP_URL = f"{WEBHOOK_HOST}/app/"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("flagbot")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚩 باز کردن پرچم",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "خوش اومدی! برای دیدن پرچم در حال اهتزاز روی دکمه‌ی زیر بزن 👇",
        reply_markup=keyboard,
    )


async def on_startup(app: web.Application):
    await bot.set_webhook(
        url=f"{WEBHOOK_HOST}{WEBHOOK_PATH}",
        drop_pending_updates=True,
    )
    log.info("Webhook set to %s%s", WEBHOOK_HOST, WEBHOOK_PATH)


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()


async def handle_webhook(request: web.Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return web.Response()


async def health(request: web.Request):
    # این مسیر فقط برای این است که Render مطمئن شود سرویس زنده است
    return web.Response(text="ربات فعال است ✅")


async def webapp_index(request: web.Request):
    index_path = os.path.join(
        os.path.dirname(__file__),
        "webapp",
        "index.html"
    )
    return web.FileResponse(index_path)


def create_app() -> web.Application:
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    # Mini App
    app.router.add_get("/app/", webapp_index)

    # فایل‌های Mini App
    app.router.add_static(
        "/app/",
        path=os.path.join(os.path.dirname(__file__), "webapp"),
        show_index=False,
    )

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
