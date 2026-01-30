# 🦂 SCORPIO | High-Performance IG Extraction Engine

**Scorpio** is a professional-grade Instagram video extraction tool built on the **Quart** (Asynchronous Flask) framework and powered by **yt-dlp**. It features a high-end "Cyber-Ops" aesthetic, glassmorphic UI, and a resilient backend designed for high-concurrency cloud deployment.

---

## ⚡ Core Features
* **Asynchronous Streaming:** Leverages `Quart` and `httpx` for non-blocking, chunked video delivery (1MB fragments) to maximize download speeds and minimize server RAM usage.
* **Anti-Sleep Engine:** Integrated background heartbeat task that pings the system every 10 minutes to prevent Render/Cloud idling (15-min sleep cycles).
* **Recalibration UI:** A futuristic glassmorphic interface featuring a **3-second "System Shake"** recalibration effect triggered on every page load/refresh.
* **Session Persistence:** Supports `instagram_cookies.txt` via environment variables to bypass rate limits and private content restrictions.
* **Auto-Reset Logic:** A strict **6-second hard-reload cycle** triggered immediately upon user interaction, ensuring the engine resets to an "Optimized" state after every fetch.

---

## 🛠️ Technical Stack
* **Backend:** Python 3.10+ (`Quart`, `yt-dlp`, `httpx`)
* **Frontend:** Tailwind CSS, Plus Jakarta Sans, Vanilla JS
* **Deployment:** Optimized for Render, Fly.io, or VPS

---

## 🚀 Deployment Guide

### 1. Environment Variables
To keep your instance active and authenticated, set the following in your hosting dashboard:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | The port the server binds to | `5000` |
| `COOKIES_CONTENT` | The raw text content of your exported Netscape cookies | `None` |
| `PUBLIC_URL` | Your live deployment URL (required for Heartbeat engine) | `https://your-app.onrender.com/health` |

### 2. Cookie Configuration
Scorpio requires Instagram cookies to maintain high-fidelity extraction rates.
1. Export your cookies from your browser in **Netscape** format.
2. Paste the raw content into the `COOKIES_CONTENT` environment variable in your host settings.
3. The engine will automatically generate the `instagram_cookies.txt` file on boot.

### 3. Local Installation
```bash
# Clone the repository
git clone [https://github.com/Motari2004/igdown](https://github.com/Motari2004/igdown)
cd igdown

# Install dependencies
pip install quart yt-dlp httpx

# Launch the engine
python app.py