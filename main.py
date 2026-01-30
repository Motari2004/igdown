from quart import Quart, render_template, request, Response
import yt_dlp
import httpx
import asyncio
import logging
import os
from urllib.parse import quote

# -----------------------------
# Configuration
# -----------------------------
# Render provides the PORT environment variable automatically
PORT = int(os.environ.get("PORT", 5000))
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
COOKIE_FILE = "instagram_cookies.txt" 

app = Quart(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("IG-Streamer")

# -----------------------------
# yt-dlp extractor
# -----------------------------
async def extract_instagram_info(url: str) -> dict:
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
    }
    
    # Check if cookie file exists before passing it
    if os.path.exists(COOKIE_FILE):
        ydl_opts["cookiefile"] = COOKIE_FILE

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info or "url" not in info:
                raise ValueError("Unable to extract video URL")
            return info

    info = await asyncio.to_thread(extract)

    return {
        "video_url": info["url"],
        "headers": info.get("http_headers", {}),
        "filename": quote(f"{info.get('title', 'instagram_video')}.mp4")
    }

# -----------------------------
# RANGE STREAMER
# -----------------------------
async def range_stream(video_url: str, base_headers: dict):
    timeout = httpx.Timeout(connect=20.0, read=300.0, write=20.0, pool=20.0)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True) as client:
        head = await client.head(video_url, headers=base_headers)
        total_size = int(head.headers.get("Content-Length", 0))
        start = 0

        while start < total_size:
            end = min(start + CHUNK_SIZE - 1, total_size - 1)
            headers = {**base_headers, "Range": f"bytes={start}-{end}"}

            async with client.stream("GET", video_url, headers=headers) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    yield chunk

            start = end + 1
            await asyncio.sleep(0)

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
async def index():
    return "IG Streamer is Running!" # Or render_template("index.html")

@app.route("/download", methods=["POST"])
async def download():
    form = await request.form
    url = form.get("url")

    if not url:
        return "❌ No URL provided", 400

    try:
        info = await extract_instagram_info(url)
        return Response(
            range_stream(info["video_url"], info["headers"]),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{info['filename']}",
                "Content-Type": "video/mp4",
                "Accept-Ranges": "bytes",
                "X-Content-Type-Options": "nosniff",
            }
        )
    except Exception as e:
        logger.exception("Download error")
        return f"❌ Error: {str(e)}", 500