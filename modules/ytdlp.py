import os, yt_dlp, logging
from typing import Optional, List, Dict
from .utils import is_cancelled, DownloadCancelled, should_update, humanbytes, format_eta, text_progress

log = logging.getLogger("ytdlp")

def list_formats(url: str, cookies: Optional[str]) -> List[Dict]:
    ydl_opts = {"quiet": True, "no_warnings": True, "simulate": True}
    if cookies and os.path.isfile(cookies): ydl_opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        fmts = []
        for f in info.get("formats", []):
            if f.get("filesize") or f.get("filesize_approx"):
                fmts.append({
                    "id": f["format_id"],
                    "res": f.get("format_note") or f.get("resolution") or f["ext"],
                    "size": f.get("filesize") or f.get("filesize_approx"),
                    "ext": f["ext"]
                })
        return fmts

def download_media(url, outdir, cookies, task_id, status_cb, fmt=None):
    os.makedirs(outdir, exist_ok=True)
    outtmpl = os.path.join(outdir, "%(title).200B [%(id)s].%(ext)s")

    def hook(d):
        if is_cancelled(task_id): raise DownloadCancelled("Cancelled by user.")
        if d["status"] in ("downloading", "finished"):
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes")
            spd = d.get("speed"); eta = d.get("eta")
            frac = (done/total*100) if total and done else 0
            bar = text_progress(frac)
            txt = f"**Downloading…** {bar} {frac:.1f}%\n⬇ {humanbytes(done)}/{humanbytes(total)} • ETA {format_eta(eta)} • ⚡ {humanbytes(spd)}/s"
            if should_update(task_id): status_cb(txt)

    opts = {
        "outtmpl": outtmpl, "quiet": True, "progress_hooks": [hook],
        "format": fmt or "bv*+ba/best", "merge_output_format": "mp4"
    }
    if cookies and os.path.isfile(cookies): opts["cookiefile"] = cookies

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get("title","file")
