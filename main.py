import os
import asyncio
import logging
from urllib.parse import quote

from quart import Quart, render_template, request, Response
import yt_dlp
import httpx

# -----------------------------
# Configuration & Environment
# -----------------------------
PORT = int(os.environ.get("PORT", 10000))
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
COOKIE_FILE = "instagram_cookies.txt"

# Securely reconstruct cookies from Environment Variable if provided
COOKIES_CONTENT = os.environ.get("COOKIES_CONTENT")
if COOKIES_CONTENT:
    with open(COOKIE_FILE, "w") as f:
        f.write(COOKIES_CONTENT)

app = Quart(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("IG-Streamer")

# -----------------------------
# yt-dlp Extractor
# -----------------------------
async def extract_instagram_info(url: str) -> dict:
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        # Allow use of cookies if the file exists
        "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
    }

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info or "url" not in info:
                raise ValueError("Unable to extract video URL")
            return info

    # Run blocking yt-dlp call in a thread to keep the loop free
    info = await asyncio.to_thread(extract)

    return {
        "video_url": info["url"],
        "headers": info.get("http_headers", {}),
        "filename": quote(f"{info.get('title', 'instagram_video')}.mp4")
    }

# -----------------------------
# Range Streamer Logic
# -----------------------------
async def range_stream(video_url: str, base_headers: dict):
    timeout = httpx.Timeout(connect=20.0, read=300.0, write=20.0, pool=20.0)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True) as client:
        # Get total size from the source
        head = await client.head(video_url, headers=base_headers)
        total_size = int(head.headers.get("Content-Length", 0))
        
        start = 0
        while start < total_size:
            end = min(start + CHUNK_SIZE - 1, total_size - 1)
            headers = {
                **base_headers,
                "Range": f"bytes={start}-{end}",
                "Connection": "keep-alive",
            }

            async with client.stream("GET", video_url, headers=headers) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    if chunk:
                        yield chunk

            start = end + 1
            await asyncio.sleep(0)  # Yield control to the event loop

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
async def index():
    # Ensure you have an index.html in a /templates folder
    # Or just return a simple string for testing:
    return "IG Streamer Docker Instance is Live."

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
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            }
        )

    except Exception as e:
        logger.exception("Download error")
        return f"❌ Error: {str(e)}", 500