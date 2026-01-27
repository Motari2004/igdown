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

    # The "Bot-Bypass" Command
    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        # Force a real browser identity
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Use Android client logic (YouTube blocks this less often)
        "--extractor-args", "youtube:player_client=android,web",
        "-f", "best[ext=mp4]/best",
        "--get-url",
        url
    ]

    # Use cookies if the file exists in your repo
    if os.path.exists("cookies.txt"):
        command.insert(1, "--cookies")
        command.insert(2, "cookies.txt")

    try:
        # We use a timeout so Render doesn't hang forever
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"yt-dlp Error: {result.stderr}")
            # Clean up the error message for the user
            if "Sign in to confirm" in result.stderr:
                raise Exception("YouTube is asking for verification. Try a different link or add cookies.")
            raise Exception("Extraction failed. The video might be restricted.")

        direct_url = result.stdout.strip()

        if not direct_url:
            raise Exception("No download link found.")

        # Browser Redirect: High speed, low RAM
        return RedirectResponse(url=direct_url)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Request took too long. YouTube is slow today.")
    except Exception as e:
        print(f"Error Log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)