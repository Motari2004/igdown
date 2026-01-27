from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import os

app = FastAPI(title="TurboStream Pro")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Base command with heavy spoofing
    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "--extractor-args", "youtube:player_client=android,web",
        "-f", "best[ext=mp4]/best",
        "--get-url"
    ]

    # CHECK FOR COOKIES: This is the critical part for Render
    if os.path.exists("cookies.txt"):
        command.extend(["--cookies", "cookies.txt"])
    
    command.append(url)

    try:
        # Run extraction
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        
        if result.returncode != 0:
            print(f"yt-dlp Error: {result.stderr}")
            if "confirm you're not a bot" in result.stderr:
                raise Exception("YouTube blocked the server. You must upload a fresh cookies.txt file.")
            raise Exception("Extraction failed.")

        direct_url = result.stdout.strip()
        if not direct_url:
            raise Exception("No URL returned.")

        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Server Log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)