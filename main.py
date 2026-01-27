from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import signal
import sys
import os

app = FastAPI(title="TurboStream Render-Safe")
templates = Jinja2Templates(directory="templates")

# Graceful exit for local Ctrl+C and Render SIGTERM
def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="Invalid URL")

    # OPTIMIZED FOR RENDER FREE TIER (512MB RAM)
    # 1. height<=720: Prevents massive RAM usage during merging
    # 2. -x 4: Limits parallel connections to reduce buffer memory
    # 3. --buffer-size: Keeps aria2c memory footprint small
    command = [
        "yt-dlp",
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x 4 -s 4 -k 1M --buffer-size=1M",
        "-o", "-", 
        "--no-playlist",
        "--quiet",
        "--no-part",
        url
    ]

    def iterfile():
        # Use a smaller bufsize (64KB) to prevent memory spikes in the Python process
        proc = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL,
            bufsize=65536 
        )
        try:
            while True:
                chunk = proc.stdout.read(65536) 
                if not chunk:
                    break
                yield chunk
        finally:
            # Clean up the subprocess to prevent 'Zombie' processes consuming RAM
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

    return StreamingResponse(
        iterfile(), 
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }
    )