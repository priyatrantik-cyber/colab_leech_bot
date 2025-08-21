import os, asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .ytdlp import list_formats, download_media
from .utils import data_paths, ensure_dirs, register_task, cancel_task, cleanup_task, DownloadCancelled, safe_edit_text, humanbytes, text_progress, should_update

log = logging.getLogger("leech")

def cancel_btn(tid): return InlineKeyboardMarkup([[InlineKeyboardButton("⛔ Cancel", callback_data=f"cancel:{tid}")]])

def register_leech_handlers(app: Client):
    @app.on_message(filters.command("leech"))
    async def cmd(_, m):
        args = m.text.split(maxsplit=1)
        if len(args)<2: return await m.reply("Usage: /leech <url>")
        url = args[1].strip()
        paths = data_paths(); ensure_dirs()
        msg = await m.reply("🔍 Fetching qualities…")
        fmts = await asyncio.get_event_loop().run_in_executor(None, lambda: list_formats(url, paths["cookies"]))
        if not fmts: return await msg.edit("❌ No formats found.")
        kb=[]; row=[]
        for i,f in enumerate(fmts[:10],1):
            label=f"{f['res']} • {humanbytes(f['size'])}"
            row.append(InlineKeyboardButton(label, callback_data=f"choose:{url}:{f['id']}"))
            if i%2==0: kb.append(row); row=[]
        if row: kb.append(row)
        await msg.edit("🎞 **Choose quality:**", reply_markup=InlineKeyboardMarkup(kb))

    @app.on_callback_query(filters.regex(r"^choose:(.+?):(.+)$"))
    async def cb(_,q):
        url,fmt=q.data.split(":",2)[1:]
        paths=data_paths()
        st=await q.message.edit("⏳ Preparing download…", reply_markup=cancel_btn(0))
        tid=st.id
        await st.edit_reply_markup(cancel_btn(tid))
        ev=register_task(tid)

        async def updater(txt): await safe_edit_text(st, f"{txt}\n\n`{url}`", reply_markup=cancel_btn(tid))

        async def runner():
            try:
                fpath,fname=await asyncio.get_event_loop().run_in_executor(None, lambda: download_media(url,paths["downloads"],paths["cookies"],tid,lambda t:asyncio.run_coroutine_threadsafe(updater(t),asyncio.get_event_loop()),fmt))
                size=os.path.getsize(fpath)
                async def up_cb(cur,tot):
                    if should_update(tid):
                        frac=cur/tot*100 if tot else 0; bar=text_progress(frac)
                        await updater(f"**Uploading…** {bar} {frac:.1f}%\n⬆ {humanbytes(cur)}/{humanbytes(tot)}")
                    if ev.is_set(): raise DownloadCancelled("Upload cancelled.")
                await q.message.reply_document(fpath,caption=f"✅ Leech complete: `{fname}`",progress=up_cb)
                await updater("✅ Done.")
            except DownloadCancelled as e: await st.edit(f"❌ Cancelled: {e}")
            except Exception as e: await st.edit(f"❌ Error: {e}")
            finally: cleanup_task(tid)
        asyncio.create_task(runner())

    @app.on_callback_query(filters.regex(r"^cancel:(\d+)$"))
    async def cancel_cb(_,q): cancel_task(int(q.data.split(":")[1])); await q.answer("Cancelling…")
