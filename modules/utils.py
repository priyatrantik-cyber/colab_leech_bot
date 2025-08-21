import os, time, asyncio, logging
from typing import Dict, Tuple
from pyrogram.errors import MessageNotModified

log = logging.getLogger("utils")

def data_paths():
    base = "./data"
    downloads = os.path.join(base, "downloads")
    cookies = os.path.join(base, "cookies.txt")
    return {"base": base, "downloads": downloads, "cookies": cookies}

def ensure_dirs():
    p = data_paths()
    os.makedirs(p["downloads"], exist_ok=True)

class DownloadCancelled(Exception):
    pass

TASK_STATE: Dict[int, Tuple[asyncio.Event, float]] = {}

def register_task(task_id: int):
    TASK_STATE[task_id] = (asyncio.Event(), 0.0)
    return TASK_STATE[task_id][0]

def cancel_task(task_id: int):
    if task_id in TASK_STATE:
        TASK_STATE[task_id][0].set()

def is_cancelled(task_id: int) -> bool:
    return task_id in TASK_STATE and TASK_STATE[task_id][0].is_set()

def cleanup_task(task_id: int):
    TASK_STATE.pop(task_id, None)

def humanbytes(size: float) -> str:
    if size is None: return "?"
    if size == 0: return "0 B"
    power = 2**10
    n = 0
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    while size >= power and n < len(units) - 1:
        size /= power; n += 1
    return f"{size:.2f} {units[n]}"

def format_eta(seconds: float) -> str:
    if not seconds or seconds == float("inf"): return "∞"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"

def text_progress(p: float, width: int = 18):
    filled = int(width * p / 100)
    return "█" * filled + "░" * (width - filled)

async def safe_edit_text(msg, txt: str, **kwargs):
    try:
        if getattr(msg, "text", None) == txt: return
        await msg.edit_text(txt, **kwargs)
    except MessageNotModified:
        pass

def should_update(task_id: int, min_interval: float = 2.0) -> bool:
    if task_id not in TASK_STATE: return True
    ev, last = TASK_STATE[task_id]
    now = time.time()
    if now - last >= min_interval:
        TASK_STATE[task_id] = (ev, now)
        return True
    return False
