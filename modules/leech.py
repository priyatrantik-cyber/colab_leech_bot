import os, asyncio, logging, uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .ytdlp import list_formats, download_media
from .utils import data_paths, ensure_dirs, register_task, cancel_task, cleanup_task, DownloadCancelled, safe_edit_text, humanbytes, text_progress, should_update

log = logging.getLogger("leech")

# Store URL per task ID
LEECH_URLS = {}

def cancel_btn(tid):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⛔ Cancel", callback_data=f"cancel:{tid}")]])

def register_leech_handlers(app: Client):
    @app.on_message(filters.command("leech"))
    async def cmd(_, m):
        args = m.text.split(maxsplit=1)
        if len(args) < 2:
            return await m.reply("Usage: /leech <url>")
        url = args[1].strip()
        paths = data_paths()
        ensure_dirs()
        msg = await m.reply("🔍 Fetching qualities…")

        # Fetch all formats (maximum quality)
        fmts = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: list_formats(url, paths["cookies"], all_formats=True)
        )
        if not fmts:
            return await msg.edit("❌ No formats found.")

        # Unique task ID
        tid = str(uuid.uuid4())[:8]
        LEECH_URLS[tid] = url

        kb = []
        row = []
        for i, f in enumerate(fmts[:10], 1):
            size_text = humanbytes(f['size']) if f['size'] else "N/A"
            label = f"{f['res']} • {size_text}"
            row.append(InlineKeyboardButton(label, callback_data=f"choose:{tid}:{f['id']}"))
            if i % 2 == 0:
                kb.append(row)
                row = []
        if row:
            kb.append(row)

        await msg.edit("🎞 Choose quality:", reply_markup=InlineKeyboardMarkup(kb))

    @app.on_callback_query(filters.regex(r"^choose:(.+?):(.+)$"))
    async def cb(_, q):
        tid, fmt = q.data.split(":")[1:]
        url = LEECH_URLS.get(tid)
        if not url:
            return await q.answer("❌ URL not found!", show_alert=True)

        paths = data_paths()
        st = await q.message.edit("⏳ Preparing download…", reply_markup=cancel_btn(0))
        download_tid = st.id
        await st.edit_reply_markup(cancel_btn(download_tid))
        ev = register_task(download_tid)

        async def updater(txt):
            await safe_edit_text(st, f"{txt}\n\n`{url}`", reply_markup=cancel_btn(download_tid))

        # Progress callback
        def progress_hook(d):
            if d['status'] == 'downloading':
                pct = d.get('_percent_str', '').strip()
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                bar = text_progress(float(pct.replace('%','')) if pct else 0)
                asyncio.get_event_loop().create_task(
                    updater(f"Downloading… {bar} {pct}\n⬆ {humanbytes(downloaded)}/{humanbytes(total)}")
                )

        async def runner():
            try:
                fpath, fname = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: download_media(
                        url, paths["downloads"], paths["cookies"], download_tid, progress_hook, fmt
                    )
                )
                async def up_cb(cur, tot):
                    if should_update(download_tid):
                        frac = cur / tot * 100 if tot else 0
                        bar = text_progress(frac)
                        await updater(f"Uploading… {bar} {frac:.1f}%\n⬆ {humanbytes(cur)}/{humanbytes(tot)}")
                    if ev.is_set(): raise DownloadCancelled("Upload cancelled.")
                await q.message.reply_document(fpath, caption=f"✅ Leech complete: `{fname}`", progress=up_cb)
                await updater("✅ Done.")
            except DownloadCancelled as e:
                await st.edit(f"❌ Cancelled: {e}")
            except Exception as e:
                await st.edit(f"❌ Error: {e}")
            finally:
                cleanup_task(download_tid)
                LEECH_URLS.pop(tid, None)

        asyncio.create_task(runner())

    @app.on_callback_query(filters.regex(r"^cancel:(\d+)$"))
    async def cancel_cb(_, q):
        cancel_task(int(q.data.split(":")[1]))
        await q.answer("Cancelling…")
