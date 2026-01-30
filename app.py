import os
import asyncio
import logging
import sys
from urllib.parse import quote
from quart import Quart, render_template, request, Response
import yt_dlp
import httpx

# -----------------------------
# Configuration & Global State
# -----------------------------
IS_RENDER = "RENDER" in os.environ
PORT = int(os.environ.get("PORT", 5000))
SELF_URL = f"http://127.0.0.1:{PORT}/health" 
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
COOKIE_FILE = "instagram_cookies.txt"

# GLOBAL POOL: This is the key to supporting many users.
# It reuses connections instead of creating new ones.
http_client = None 

# SEMAPHORE: Limits heavy CPU extraction tasks to 10 at a time 
# while allowing infinite streaming.
extraction_semaphore = asyncio.Semaphore(10)

app = Quart(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] Scorpio-Engine: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("Scorpio-DL")

# -----------------------------
# Engine Lifecycle
# -----------------------------
@app.before_serving
async def startup():
    global http_client
    # Initialize a high-capacity connection pool
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    timeout = httpx.Timeout(20.0, read=None)
    http_client = httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True)
    
    # Start Keep-Alive
    app.add_background_task(keep_alive)
    logger.info("🚀 Scorpio Core v2.5 initialized with Global Connection Pool")

@app.after_serving
async def shutdown():
    await http_client.aclose()

# -----------------------------
# Anti-Sleep Engine
# -----------------------------
async def keep_alive():
    await asyncio.sleep(10)
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get(SELF_URL)
            logger.info("❤️ HEARTBEAT: Engine Active")
        except Exception as e:
            logger.warning(f"💔 HEARTBEAT FAIL: {e}")
        await asyncio.sleep(300) 

# -----------------------------
# High-Concurrency Extraction
# -----------------------------
async def extract_instagram_info(url: str) -> dict:
    # Use semaphore to prevent CPU spikes during heavy traffic
    async with extraction_semaphore:
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(extract)
        return {
            "video_url": info["url"],
            "headers": info.get("http_headers", {}),
            "filename": quote(f"{info.get('title', 'scorpio_video')}.mp4")
        }

async def range_stream(video_url: str, base_headers: dict):
    """Uses the global http_client to stream data efficiently."""
    try:
        # Check size quickly
        head = await http_client.head(video_url, headers=base_headers)
        total_size = int(head.headers.get("Content-Length", 0))
    except:
        total_size = 0 

    start = 0
    while True:
        end = min(start + CHUNK_SIZE - 1, total_size - 1) if total_size else start + CHUNK_SIZE - 1
        headers = {**base_headers, "Range": f"bytes={start}-{end}"}

        try:
            async with http_client.stream("GET", video_url, headers=headers) as r:
                if r.status_code == 416: break
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    yield chunk
        except:
            break

        if total_size and end >= total_size - 1: break
        start = end + 1
        await asyncio.sleep(0) # Yield control to other users

# -----------------------------
# Routes
# -----------------------------
@app.route("/health")
async def health():
    return {"status": "optimized", "connections": "active"}, 200

@app.route("/")
async def index():
    return await render_template("index.html")

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
                "X-Engine": "Scorpio-MultiUser-V2"
            }
        )
    except Exception as e:
        return f"❌ Scorpio High-Traffic Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)