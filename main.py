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

    format_selector = "best[ext=mp4]/best"
    
    # We use 'ios' first as it is currently the most resilient to 'Sign-in' blocks
    # 'android_test' is a hidden client that sometimes bypasses IP bans
    extractor_args = "youtube:player_client=ios,android_test,web_embedded;player_skip=configs,js"

    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-check-certificate",
        "--extractor-args", extractor_args,
        "--force-ipv4", # Render uses IPv6 often, which YouTube flags faster
        "-f", format_selector,
        "--get-url",
        url
    ]

    try:
        # Attempt extraction
        result = subprocess.run(command, capture_output=True, text=True, timeout=40)
        
        if result.returncode != 0:
            # Fallback to the 'tv' client if mobile fails
            fallback_command = [
                "yt-dlp", "--quiet", "-f", "best", "--get-url",
                "--extractor-args", "youtube:player_client=tv", url
            ]
            result = subprocess.run(fallback_command, capture_output=True, text=True, timeout=40)
            
            if result.returncode != 0:
                # If everything fails, it's a hard IP ban from YouTube
                print(f"Banned Error: {result.stderr}")
                raise Exception("YouTube is blocking this server. Try again in a few minutes.")

        direct_url = result.stdout.strip()
        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Detailed Log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)