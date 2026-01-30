# 🦂 SCORPIO | High-Performance IG Extraction Engine

**Scorpio** is a professional-grade Instagram video downloader built on the **Quart** (Asynchronous Flask) framework and powered by **yt-dlp**. It features a high-end "Cyber-Ops" aesthetic, glassmorphic UI, and a resilient backend designed for cloud deployment.



## ⚡ Core Features
* **Asynchronous Streaming:** Leverages `Quart` and `httpx` for non-blocking, chunked video delivery (1MB chunks).
* **Anti-Sleep Engine:** Integrated background heartbeat task that pings the system every 10 minutes to prevent Render/Cloud idling.
* **Professional UI:** A futuristic glassmorphic interface featuring a 3-second "System Shake" recalibration effect on every page load.
* **Session Persistence:** Supports `instagram_cookies.txt` via environment variables to bypass rate limits and private content restrictions.
* **Auto-Reset Logic:** A strict 6-second cooldown cycle from execution to page reload, ensuring a fresh state for batch processing.

---

## 🛠️ Technical Stack
* **Backend:** Python 3.10+ (Quart, yt-dlp, httpx)
* **Frontend:** Tailwind CSS, Plus Jakarta Sans, Vanilla JS
* **Deployment:** Optimized for Render, Fly.io, or Heroku

---

## 🚀 Deployment Guide

### 1. Environment Variables
To keep your instance alive and authenticated, set the following in your hosting dashboard:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | The port the server binds to | `5000` |
| `COOKIES_CONTENT` | The raw text content of your exported cookies file | `None` |
| `PUBLIC_URL` | Your live deployment URL (required for Heartbeat) | `Render URL` |

### 2. Cookie Configuration
Scorpio requires Instagram cookies to maintain a high "Fidelity" extraction rate.
1. Export your cookies in Netscape format.
2. Paste the content into the `COOKIES_CONTENT` environment variable.
3. The engine will automatically generate `instagram_cookies.txt` on boot.

### 3. Local Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd scorpio

# Install dependencies
pip install quart yt-dlp httpx

# Launch the engine
python app.py