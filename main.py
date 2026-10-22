"""Orkestrator.  Ishlatish:
    python main.py generate            # ssenariy -> ovoz -> tasvir -> montaj  (output/final.mp4)
    python main.py publish             # output/final.mp4 ni Telegram/YouTube/Instagram'ga joylash
    python main.py all                 # ikkalasi ketma-ket
    python main.py generate --topic "Mavzu"   # mavzuni qo'lda berish
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from imperiya import config
from imperiya.editor import assemble
from imperiya.publisher import publish_all
from imperiya.scriptwriter import write_script
from imperiya.visual import paint
from imperiya.voice import narrate

META = config.OUTPUT / "meta.json"
FINAL = config.OUTPUT / "final.mp4"


def pick_topic() -> str:
    topics = [t.strip() for t in (config.ROOT / "topics.txt").read_text(encoding="utf-8").splitlines() if t.strip()]
    return topics[datetime.date.today().timetuple().tm_yday % len(topics)]


def generate(topic: str) -> None:
    config.OUTPUT.mkdir(exist_ok=True)
    config.WORK.mkdir(exist_ok=True)
    print(f"[1/4] Ssenariy: {topic}")
    script = write_script(topic)
    print(f"      model: {script['model']}, sahnalar: {len(script['scenes'])}")
    print("[2/4] Ovoz")
    scenes = narrate(script["scenes"], config.WORK)
    print("[3/4] Tasvirlar")
    scenes = paint(scenes, config.WORK, seed=datetime.date.today().toordinal())
    print("[4/4] Montaj")
    assemble(scenes, config.WORK, FINAL)
    META.write_text(json.dumps({k: script[k] for k in ("title", "description", "hashtags")},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tayyor: {FINAL}")


def publish() -> None:
    if not FINAL.exists() or not META.exists():
        sys.exit("Avval `python main.py generate` ni ishga tushiring.")
    meta = json.loads(META.read_text(encoding="utf-8"))
    results = publish_all(FINAL, meta)
    print("\n".join(results))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")  # GitHub Actions run sahifasida ko'rinadi
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### Nashr natijalari\n" + "\n".join(f"- {r}" for r in results) + "\n")
    if any("XATO" in r for r in results):
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["generate", "publish", "all"])
    ap.add_argument("--topic", default="")
    args = ap.parse_args()
    if args.stage in ("generate", "all"):
        generate(args.topic or pick_topic())
    if args.stage in ("publish", "all"):
        publish()
