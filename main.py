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

    # This attempts to find a single file that works in a browser redirect
    # We prioritize mp4 for compatibility
    format_selector = "best[ext=mp4]/best"

    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        # Use a very specific mobile user agent which is less likely to be blocked
        "--user-agent", "Mozilla/5.0 (Android 14; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0",
        # These args help bypass the "Sign in" requirement
        "--extractor-args", "youtube:player_client=ios,web;player_skip=configs,js",
        "-f", format_selector,
        "--get-url"
    ]

    if os.path.exists("cookies.txt"):
        command.extend(["--cookies", "cookies.txt"])
    
    command.append(url)

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            error_msg = result.stderr.lower()
            print(f"Extraction Error: {result.stderr}")
            
            # If blocked, try one last time without cookies but with a different client
            if "sign in" in error_msg or "403" in error_msg:
                command_alt = [
                    "yt-dlp", "--quiet", "-f", "best", "--get-url",
                    "--extractor-args", "youtube:player_client=mweb", url
                ]
                result = subprocess.run(command_alt, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception("YouTube blocked this request. Refresh cookies.txt.")
            else:
                raise Exception("This video is restricted or unavailable.")

        direct_url = result.stdout.strip()
        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Final Error Log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)