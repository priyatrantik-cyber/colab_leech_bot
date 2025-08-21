import yt_dlp
import os

def list_formats(url, cookies_path=None, all_formats=False):
    """
    Return list of available formats for a URL.
    Supports maximum quality and all sites.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "cookiefile": cookies_path if cookies_path and os.path.exists(cookies_path) else None,
        "format": "bestvideo+bestaudio/best" if all_formats else "best",
        "ignoreerrors": True,
        "merge_output_format": "mp4",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            fmts = []
            for f in info.get("formats", []):
                if f.get("filesize") is None:
                    size = 0
                else:
                    size = f.get("filesize")
                res = f.get("format_note") or f"{f.get('height','')}p"
                fmts.append({
                    "id": f["format_id"],
                    "res": res,
                    "size": size
                })
            return fmts
    except Exception:
        return []

def download_media(url, download_path, cookies_path, task_id, progress_callback, format_id=None):
    """
    Download media using yt-dlp.
    Supports maximum sites including adult/HLS/m3u8.
    """
    ydl_opts = {
        "outtmpl": f"{download_path}/%(title)s.%(ext)s",
        "cookiefile": cookies_path if cookies_path and os.path.exists(cookies_path) else None,
        "format": format_id if format_id else "bestvideo+bestaudio/best",
        "noplaylist": True,
        "progress_hooks": [progress_callback],
        "merge_output_format": "mp4",
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        fname = ydl.prepare_filename(info)
        return fname, os.path.basename(fname)
