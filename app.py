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
PORT = int(os.environ.get("PORT", 5000))
# Your specific Render URL to prevent idling
PUBLIC_URL = "https://igdown-01en.onrender.com/health"
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
COOKIE_FILE = "instagram_cookies.txt"

# Handle Cookies from Environment
COOKIES_CONTENT = os.environ.get("COOKIES_CONTENT")
if COOKIES_CONTENT:
    with open(COOKIE_FILE, "w") as f:
        f.write(COOKIES_CONTENT)

app = Quart(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("Scorpio-DL")

# -----------------------------
# Anti-Sleep Engine (External Ping)
# -----------------------------
async def keep_alive():
    """Background task to ping the public URL every 10 minutes."""
    await asyncio.sleep(20) # Initial boot delay
    logger.info(f"🚀 Anti-Sleep Engine targeting: {PUBLIC_URL}")
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            try:
                # Pinging the PUBLIC URL tells Render the service is in use
                response = await client.get(PUBLIC_URL, timeout=30.0)
                logger.info(f"❤️ HEARTBEAT SUCCESS: [Status {response.status_code}] Engine Active")
            except Exception as e:
                logger.warning(f"💔 HEARTBEAT DELAYED: {e}")
            
            # Ping every 10 minutes (600 seconds)
            # Render sleeps after 15 mins of inactivity
            await asyncio.sleep(600) 

@app.before_serving
async def startup_tasks():
    app.add_background_task(keep_alive)

# -----------------------------
# Routes
# -----------------------------
@app.route("/health")
async def health():
    """Endpoint for keep-alive pings."""
    return {"status": "optimized", "engine": "scorpio-v2.5", "state": "online"}, 200

@app.route("/")
async def index():
    return await render_template("index.html")

# -----------------------------
# yt-dlp & Streamer Logic
# -----------------------------
async def extract_instagram_info(url: str) -> dict:
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info or "url" not in info:
                raise ValueError("Unable to extract video URL")
            return info

    info = await asyncio.to_thread(extract)
    
    # Clean filename
    raw_title = info.get('title', 'scorpio_video')
    clean_filename = "".join([c for c in raw_title if c.isalnum() or c in (' ', '_')]).strip()
    
    return {
        "video_url": info["url"],
        "headers": info.get("http_headers", {}),
        "filename": quote(f"{clean_filename}.mp4")
    }

async def range_stream(video_url: str, base_headers: dict):
    timeout = httpx.Timeout(connect=20.0, read=None, write=20.0, pool=20.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            head = await client.head(video_url, headers=base_headers)
            total_size = int(head.headers.get("Content-Length", 0))
        except Exception:
            total_size = 0 

        start = 0
        while True:
            end = start + CHUNK_SIZE - 1
            if total_size and end >= total_size: end = total_size - 1
            headers = {**base_headers, "Range": f"bytes={start}-{end}", "Connection": "keep-alive"}

            try:
                async with client.stream("GET", video_url, headers=headers) as r:
                    if r.status_code == 416: break
                    r.raise_for_status()
                    async for chunk in r.aiter_bytes():
                        if chunk: yield chunk
            except Exception:
                break

            if total_size and end >= total_size - 1: break
            start = end + 1
            await asyncio.sleep(0.01) # Yield to event loop

@app.route("/download", methods=["POST"])
async def download():
    form = await request.form
    url = form.get("url")
    if not url: return "❌ No URL provided", 400
    try:
        info = await extract_instagram_info(url)
        return Response(
            range_stream(info["video_url"], info["headers"]),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{info['filename']}",
                "Content-Type": "video/mp4",
                "Accept-Ranges": "bytes",
            }
        )
    except Exception as e:
        logger.exception("Extraction failed")
        return f"❌ Scorpio Error: {str(e)}", 500

# -----------------------------
# Deployment Setup
# -----------------------------
if __name__ == "__main__":
    # Local development run
    app.run(host="0.0.0.0", port=PORT, debug=True)
