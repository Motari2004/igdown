import os
import asyncio
import logging
import sys
from urllib.parse import quote

from quart import Quart, render_template, request, Response
import yt_dlp
import httpx

# -----------------------------
# Configuration & Environment
# -----------------------------
# Checks if running on Render; otherwise defaults to port 5000 for local dev
IS_RENDER = "RENDER" in os.environ
PORT = int(os.environ.get("PORT", 5000))
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
COOKIE_FILE = "instagram_cookies.txt"

# Securely reconstruct cookies from Environment Variable if provided (Render/Docker)
COOKIES_CONTENT = os.environ.get("COOKIES_CONTENT")
if COOKIES_CONTENT:
    with open(COOKIE_FILE, "w") as f:
        f.write(COOKIES_CONTENT)

app = Quart(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("Scorpio-DL")

# -----------------------------
# yt-dlp Extractor
# -----------------------------
async def extract_instagram_info(url: str) -> dict:
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
    }

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
        "filename": quote(f"{info.get('title', 'scorpio_video')}.mp4")
    }

# -----------------------------
# Range Streamer Logic
# -----------------------------
async def range_stream(video_url: str, base_headers: dict):
    timeout = httpx.Timeout(connect=20.0, read=300.0, write=20.0, pool=20.0)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True) as client:
        # Get total size from the source
        try:
            head = await client.head(video_url, headers=base_headers)
            total_size = int(head.headers.get("Content-Length", 0))
        except:
            total_size = 0 # Fallback for sources hidden behind proxy

        start = 0
        while True:
            end = start + CHUNK_SIZE - 1
            if total_size and end >= total_size:
                end = total_size - 1

            headers = {
                **base_headers,
                "Range": f"bytes={start}-{end}",
                "Connection": "keep-alive",
            }

            async with client.stream("GET", video_url, headers=headers) as r:
                # If we get a 416, we've reached the end of the stream
                if r.status_code == 416:
                    break
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    if chunk:
                        yield chunk

            if total_size and end >= total_size - 1:
                break
                
            start = end + 1
            await asyncio.sleep(0) 

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
async def index():
    # Serves the premium index.html from /templates
    return await render_template("index.html")

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

# -----------------------------
# Local Execution Entry Point
# -----------------------------
if __name__ == "__main__":
    # This block only runs when you execute 'python app.py'
    logger.info(f"Starting Scorpio Local Dev Server on http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)