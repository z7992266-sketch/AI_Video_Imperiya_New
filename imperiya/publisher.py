"""5-agent: Nashr qiluvchi. Telegram, YouTube Shorts, Instagram Reels (rasmiy API'lar orqali).
Kalitlari berilmagan platforma o'tkazib yuboriladi."""
import time
from pathlib import Path

import requests

from . import config


def caption(meta: dict) -> str:
    tags = " ".join(meta.get("hashtags", []))
    return f"{meta['title']}\n\n{meta.get('description', '')}\n\n{tags}".strip()


def to_telegram(video: Path, meta: dict) -> str:
    token, chat = config.get("TELEGRAM_BOT_TOKEN"), config.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return "telegram: o'tkazib yuborildi (kalit yo'q)"
    with open(video, "rb") as fh:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendVideo",
            data={"chat_id": chat, "caption": caption(meta)[:1000], "supports_streaming": "true"},
            files={"video": fh}, timeout=300,
        )
    r.raise_for_status()
    return "telegram: yuborildi"


def _yt_token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": config.get("YT_CLIENT_ID"), "client_secret": config.get("YT_CLIENT_SECRET"),
        "refresh_token": config.get("YT_REFRESH_TOKEN"), "grant_type": "refresh_token",
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def to_youtube(video: Path, meta: dict) -> str:
    if not (config.get("YT_CLIENT_ID") and config.get("YT_CLIENT_SECRET") and config.get("YT_REFRESH_TOKEN")):
        return "youtube: o'tkazib yuborildi (kalit yo'q)"
    token = _yt_token()
    body = {
        "snippet": {"title": (meta["title"] + " #Shorts")[:100], "description": caption(meta) + "\n#Shorts",
                    "categoryId": "22"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {token}", "X-Upload-Content-Type": "video/mp4"},
        json=body, timeout=60,
    )
    init.raise_for_status()
    with open(video, "rb") as fh:
        up = requests.put(init.headers["Location"], data=fh, headers={"Content-Type": "video/mp4"}, timeout=600)
    up.raise_for_status()
    return f"youtube: yuklandi (id={up.json().get('id')})"


def to_instagram(meta: dict) -> str:
    uid, token, url = config.get("IG_USER_ID"), config.get("IG_ACCESS_TOKEN"), config.get("VIDEO_PUBLIC_URL")
    if not (uid and token and url):
        return "instagram: o'tkazib yuborildi (kalit yoki VIDEO_PUBLIC_URL yo'q)"
    base = "https://graph.facebook.com/v21.0"
    c = requests.post(f"{base}/{uid}/media", data={
        "media_type": "REELS", "video_url": url, "caption": caption(meta)[:2000], "access_token": token}, timeout=60)
    c.raise_for_status()
    creation = c.json()["id"]
    for _ in range(30):  # ~5 daqiqagacha kutamiz
        st = requests.get(f"{base}/{creation}", params={"fields": "status_code", "access_token": token}, timeout=30)
        code = st.json().get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Instagram video qayta ishlashda xato: {st.text}")
        time.sleep(10)
    p = requests.post(f"{base}/{uid}/media_publish", data={"creation_id": creation, "access_token": token}, timeout=60)
    p.raise_for_status()
    return "instagram: e'lon qilindi"


def publish_all(video: Path, meta: dict) -> list[str]:
    results = []
    for name, fn in (("telegram", lambda: to_telegram(video, meta)),
                     ("youtube", lambda: to_youtube(video, meta)),
                     ("instagram", lambda: to_instagram(meta))):
        try:
            results.append(fn())
        except Exception as exc:  # bitta platforma xatosi boshqalarga halaqit bermasin
            results.append(f"{name}: XATO - {exc}")
    return results
