from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import signal
import sys
import shlex

app = FastAPI(title="Turbo Stream Downloader")
templates = Jinja2Templates(directory="templates")

# Immediate exit on Ctrl+C for the server process
def signal_handler(sig, frame):
    print("\nForce quitting server...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="Invalid URL")

    # The Turbo Settings: 
    # 1. --downloader aria2c: Parallel connection king
    # 2. --downloader-args: Open 16 connections per server
    command = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x 16 -s 16 -k 1M",
        "-o", "-", # Stream to stdout
        "--no-playlist",
        "--quiet",
        "--no-part", # Don't use .part files, stream raw
        url
    ]

    def iterfile():
        # Start the process
        proc = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL,
            bufsize=1024*1024 # 1MB buffer for smoother streaming
        )
        try:
            while True:
                # Read in 128KB chunks for high-speed throughput
                chunk = proc.stdout.read(1024 * 128)
                if not chunk:
                    break
                yield chunk
        finally:
            # If the user cancels the download in browser, kill the process
            proc.terminate()
            proc.wait()

    return StreamingResponse(
        iterfile(), 
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="fast_video.mp4"',
            "Connection": "keep-alive"
        }
    )