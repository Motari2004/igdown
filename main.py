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

    # This selection string looks for the best single file (video+audio) 
    # to avoid "Format not available" errors.
    format_selector = "best" 

    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "--extractor-args", "youtube:player_client=android,web",
        "-f", format_selector,
        "--get-url"
    ]

    # Use cookies if the file exists
    if os.path.exists("cookies.txt"):
        command.extend(["--cookies", "cookies.txt"])
    
    command.append(url)

    try:
        # Increase timeout to 30s because Render can be slow
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            error_msg = result.stderr.lower()
            print(f"Extraction Error: {result.stderr}")
            
            if "sign in" in error_msg:
                raise Exception("YouTube blocked this request. Refresh your cookies.txt.")
            elif "format is not available" in error_msg:
                raise Exception("This specific quality isn't available. Try another video.")
            else:
                raise Exception("Could not extract video. YouTube might be throttling the server.")

        direct_url = result.stdout.strip()
        
        if not direct_url:
            raise Exception("No direct URL found.")

        # Redirect the user's browser to the actual file
        return RedirectResponse(url=direct_url)

    except Exception as e:
        print(f"Final Error Log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)