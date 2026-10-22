"""1-agent: Ssenarist. OpenRouter'ning faqat BEPUL (:free) modellaridan foydalanadi."""
import json
import re

import requests

from . import config

SYSTEM = (
    "Sen qisqa vertikal videolar (Reels/Shorts) uchun o'zbek tilida (lotin yozuvi) ssenariy yozadigan "
    "professional ssenaristsan. Faqat JSON qaytar, boshqa matn yozma."
)

USER_TMPL = """Mavzu: {topic}

Quyidagi JSON tuzilmasida ssenariy yoz:
{{
  "title": "jalb qiluvchi sarlavha (60 belgigacha)",
  "description": "1-2 gaplik tavsif",
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "scenes": [
    {{"text": "o'zbekcha 1 ta qisqa gap (diktor matni)", "image_prompt": "inglizcha, vizual tasvir tavsifi"}}
  ]
}}

Qoidalar: 5 dan 7 gacha sahna; har sahna matni 8-18 so'z; birinchi sahna e'tiborni tortadigan savol yoki fakt bo'lsin;
oxirgi sahna chaqiriq (like/obuna) bo'lsin; image_prompt'da matn yoki yozuv bo'lmasin."""


def _headers() -> dict:
    key = config.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY o'rnatilmagan (.env yoki GitHub Secrets).")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def free_models() -> list[str]:
    explicit = [m.strip() for m in config.get("OPENROUTER_MODELS").split(",") if m.strip()]
    if explicit:
        return explicit
    base = config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    resp = requests.get(f"{base}/models", headers=_headers(), timeout=30)
    resp.raise_for_status()
    found = []
    for m in resp.json().get("data", []):
        pricing = m.get("pricing", {})
        if str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0" and m["id"].endswith(":free"):
            found.append(m["id"])
    if not found:
        raise RuntimeError("Bepul model topilmadi.")
    return found


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start : end + 1])
    scenes = [s for s in data.get("scenes", []) if s.get("text") and s.get("image_prompt")]
    if len(scenes) < 3:
        raise ValueError("Sahnalar yetarli emas")
    data["scenes"] = scenes[:8]
    data.setdefault("title", "Qiziqarli video")
    data.setdefault("description", "")
    data.setdefault("hashtags", [])
    return data


def write_script(topic: str) -> dict:
    base = config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    errors = []
    for model in free_models()[:8]:
        try:
            resp = requests.post(
                f"{base}/chat/completions",
                headers=_headers(),
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": USER_TMPL.format(topic=topic)},
                    ],
                    "temperature": 0.8,
                },
                timeout=120,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            script = _parse(content)
            script["model"] = model
            return script
        except Exception as exc:  # keyingi bepul modelga o'tamiz
            errors.append(f"{model}: {exc}")
    raise RuntimeError("Hech bir bepul model javob bermadi:\n" + "\n".join(errors))
