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

    # Prioritize MP4 and single-file streams for direct browser redirection
    format_selector = "best[ext=mp4]/best"

    # We use multiple client types to bypass the "Sign in" requirement.
    # 'tv' and 'web_embedded' are currently the most reliable for non-cookie sessions.
    extractor_args = "youtube:player_client=tv,web_embedded;player_skip=configs,js"

    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--extractor-args", extractor_args,
        "-f", format_selector,
        "--get-url",
        url
    ]

    try:
        # Run with a 30s timeout
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            error_msg = result.stderr.lower()
            # If the TV client fails, try the mobile web fallback
            if "sign in" in error_msg or "403" in error_msg:
                fallback_command = [
                    "yt-dlp", "--quiet", "-f", "best", "--get-url",
                    "--extractor-args", "youtube:player_client=mweb", url
                ]
                result = subprocess.run(fallback_command, capture_output=True, text=True, timeout=30)
                
            if result.returncode != 0:
                raise Exception("YouTube is blocking this request. Try a different video or wait a few minutes.")

        direct_url = result.stdout.strip()
        
        # Security: ensure we actually got a URL back
        if not direct_url.startswith("http"):
            raise Exception("Failed to retrieve a valid stream URL.")

        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)