import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import COOKIES_DIR, ensure_dirs

COOKIES_FILE = os.path.join(COOKIES_DIR, "cookies.txt")

def register_cookie_handlers(app: Client):

    @app.on_callback_query(filters.regex(r"^cookies:add$"))
    async def add_cookies_cb(_, cq):
        ensure_dirs()
        if os.path.exists(COOKIES_FILE):
            await cq.answer("⚠ Cookies already exist! Remove first to add new.", show_alert=True)
        else:
            await cq.answer("📥 Please send your cookies.txt file in chat.", show_alert=True)

    @app.on_callback_query(filters.regex(r"^cookies:remove$"))
    async def remove_cookies_cb(_, cq):
        ensure_dirs()
        if os.path.exists(COOKIES_FILE):
            os.remove(COOKIES_FILE)
            await cq.answer("✅ cookies.txt removed.", show_alert=True)
        else:
            await cq.answer("⚠ No cookies.txt found.", show_alert=True)

    @app.on_message(filters.document & filters.private)
    async def save_cookies_file(_, m):
        ensure_dirs()
        if not m.document.file_name.endswith(".txt"):
            return await m.reply("❌ Only .txt files are allowed for cookies.")
        # Save uploaded cookies.txt
        file_path = COOKIES_FILE
        await m.download(file_path)
        await m.reply("✅ cookies.txt saved successfully!")
