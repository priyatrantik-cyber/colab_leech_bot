import os, asyncio, threading, time

DOWNLOAD_DIR = "./data/downloads"
COOKIES_DIR = "./data/cookies"

TASKS = {}

def ensure_dirs():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(COOKIES_DIR, exist_ok=True)

def data_paths():
    return {
        "downloads": DOWNLOAD_DIR,
        "cookies": os.path.join(COOKIES_DIR, "cookies.txt")
    }

def humanbytes(size):
    if not size:
        return "0B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}PB"

def text_progress(percent, length=20):
    filled = int(length * percent / 100)
    return "█"*filled + "░"*(length-filled)

def register_task(tid):
    TASKS[tid] = threading.Event()
    return TASKS[tid]

def cancel_task(tid):
    if tid in TASKS:
        TASKS[tid].set()

def cleanup_task(tid):
    TASKS.pop(tid, None)

def should_update(tid):
    return tid in TASKS and not TASKS[tid].is_set()

async def safe_edit_text(msg, text, **kwargs):
    try:
        await msg.edit_text(text, **kwargs)
    except Exception:
        pass

class DownloadCancelled(Exception):
    pass
