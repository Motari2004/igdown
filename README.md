# 🦂 SCORPIO | High-Performance IG Extraction Engine
![System Version](https://img.shields.io/badge/System-v2.5_Online-indigo?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)
![Engine](https://img.shields.io/badge/Engine-CORE--V2-blue?style=for-the-badge)

**Scorpio** is a professional-grade, asynchronous Instagram media extraction tool. Built with a cyber-ops aesthetic, it utilizes a **Quart** backend and **yt-dlp** to deliver original-source media streams directly to the user with zero server-side storage overhead.



---

## ⚡ Core Specifications

| Feature | Specification |
| :--- | :--- |
| **Backend Architecture** | Asynchronous Python (Quart) |
| **Stream Logic** | 1MB Fragmented Chunking (`httpx`) |
| **UI Framework** | Tailwind CSS + Glassmorphism v3 |
| **Extraction Engine** | `yt-dlp` Core-V2 Optimized |
| **Stability** | Integrated Anti-Sleep Heartbeat Engine |

---

## 💎 Exclusive Features

### 🛠️ Anti-Sleep Heartbeat
Designed for **Render** and **Heroku** deployments. Scorpio includes a background task that pings its own `/health` endpoint every 10 minutes, preventing the 15-minute inactivity "idle sleep" common in free-tier hosting.

### 🧬 Recalibration UI
On every system load or refresh, the interface performs a **3-second System Shake**. This visual cue confirms the engine is recalibrating its gateway and clearing the pipeline for a fresh extraction.

### ⏱️ 6-Second Auto-Reset
To ensure maximum reliability during batch extraction, the system locks the UI upon click and triggers a hard-reload exactly **6 seconds** later. This keeps the extraction engine "Optimized" and prevents memory leaks from stalled stream requests.

---

## 🚀 Rapid Deployment

### 1. Configure Environment
Set these variables in your deployment dashboard (Render/Fly.io/Heroku):

* `COOKIES_CONTENT`: Paste the raw text from your exported Netscape cookies file.
* `PUBLIC_URL`: Your live app URL (e.g., `https://scorpio.onrender.com/health`).
* `PORT`: `5000`

### 2. Local Installation
Copy and execute the following commands in your terminal:

```bash
# Clone the repository
git clone [https://github.com/Motari2004/igdown](https://github.com/Motari2004/igdown)

# Enter the system directory
cd igdown

# Install the extraction stack
pip install quart yt-dlp httpx

# Boot the engine
python app.py