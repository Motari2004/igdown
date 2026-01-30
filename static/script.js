async function download() {
  const url = document.getElementById("url").value;
  const btn = document.querySelector("button");
  const status = document.getElementById("status");

  if (!url) {
    status.textContent = "⚠️ Paste an Instagram link";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Downloading...";
  status.textContent = "⏳ Fetching video...";

  const res = await fetch("/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });

  if (!res.ok) {
    status.textContent = "❌ Failed to download";
    btn.disabled = false;
    btn.textContent = "Download";
    return;
  }

  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "instagram_video.mp4";
  document.body.appendChild(a);
  a.click();
  a.remove();

  status.textContent = "✅ Download started";
  btn.disabled = false;
  btn.textContent = "Download";
}
