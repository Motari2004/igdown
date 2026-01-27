import os
import subprocess
import uvicorn
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="TurboStream Pro")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # Format: best mp4 available for direct browser playback
    format_selector = "best[ext=mp4]/best"

    # STRATEGY: Use the Android Music client. 
    # This is currently the most 'invisible' client for cloud IPs.
    extractor_args = "youtube:player_client=android_music,android;player_skip=configs,js"

    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--no-check-certificate",
        "--socket-timeout", "10",
        "--referer", "https://www.youtube.com/",
        "--extractor-args", extractor_args,
        "-f", format_selector,
        "--get-url",
        url
    ]

    try:
        # Initial attempt with Mobile/Music clients
        process = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if process.returncode != 0:
            error_msg = process.stderr.lower()
            print(f"Primary Client Failed: {process.stderr}")
            
            # FALLBACK: If Android fails, try the TV client (last resort before block)
            fallback_args = "youtube:player_client=tv,web_embedded"
            fallback_command = [
                "yt-dlp", "--quiet", "-f", format_selector, "--get-url",
                "--extractor-args", fallback_args, url
            ]
            process = subprocess.run(fallback_command, capture_output=True, text=True, timeout=30)
            
            if process.returncode != 0:
                # Direct message to user about IP throttling
                raise Exception("YouTube has temporarily flagged this server's IP. Try again in a few minutes.")

        direct_url = process.stdout.strip()
        
        if not direct_url.startswith("http"):
            raise Exception("No valid stream URL found.")

        # Redirect the user to the direct video stream
        return RedirectResponse(url=direct_url)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Request timed out. YouTube is taking too long to respond.")
    except Exception as e:
        print(f"Log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Render provides the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)