from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import os
import json

app = FastAPI(title="TurboStream Pro")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        # We fetch the URL and the Title as JSON for accuracy
        command = [
            "yt-dlp",
            "--quiet",
            "--no-warnings",
            "--no-playlist",
            "-f", "best[ext=mp4]/best",
            "--get-url",
            url
        ]
        
        # Run command
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(result.stderr)

        direct_url = result.stdout.strip()

        if not direct_url:
            raise Exception("Could not extract stream URL")

        # Redirect browser to the direct source (High Speed, 0 RAM usage)
        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Extraction Error: {e}")
        raise HTTPException(status_code=500, detail="Video unavailable or unsupported.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)