import os
from pyrogram import filters
from .utils import data_paths, ensure_dirs
EXPECT=set()

def register_cookie_handlers(app):
    @app.on_callback_query(filters.regex("^cookies:add$"))
    async def add(_,q):
        ensure_dirs(); EXPECT.add(q.from_user.id)
        await q.message.reply("📄 Send `cookies.txt` file as document."); await q.answer()

    @app.on_callback_query(filters.regex("^cookies:remove$"))
    async def rem(_,q):
        p=data_paths()["cookies"]
        if os.path.isfile(p): os.remove(p); await q.message.reply("🗑 cookies.txt removed.")
        else: await q.message.reply("ℹ️ No cookies.txt found.")
        await q.answer()

    @app.on_message(filters.document)
    async def doc(_,m):
        if m.from_user and m.from_user.id in EXPECT:
            if m.document.file_name.lower()!="cookies.txt": return await m.reply("⚠️ Name must be `cookies.txt`")
            p=data_paths()["cookies"]; ensure_dirs()
            await m.download(file_name=p); EXPECT.discard(m.from_user.id)
            await m.reply("✅ cookies.txt saved.")
