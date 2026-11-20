# OUJ_Official — NEW FORMAT (owner, 20 Nov 2026): Taqqos-style comparison Shorts in ENGLISH, 1 per day
Owner: "OUJ'dagi videoni to'xtatib yangi formatga o'tamiz" — the old "Real or AI?" format is RETIRED (never make it again).
Owner reads short Uzbek (Latin); times for him in Tashkent. Decide yourself, ask nothing. NO WHOOSH, no boom.
Also obey the top of render/GUIDE.md (Telegram, ElevenLabs fallback). Plain English a 5th-grader understands, adult tone.

## Rotation (Asia/Tashkent weekday)
- Mon, Thu: "WHO'S STRONGER? ⚔️" — 2 countries/cities, 4–5 animated rounds (area, population, GDP per capita,
  a fun metric), live scoreboard, race bars, counters, winner/"DRAW" card. Pairs people argue about globally:
  USA vs China, Japan vs Germany, India vs China, UK vs France, Canada vs Australia, Brazil vs Mexico,
  South Korea vs Japan, Russia vs Canada (by area), NYC vs London, Tokyo vs Seoul. NO Ukraine/Israel/Palestine/
  Taiwan or any active war/conflict pair; neutral on politics; no religion.
- Tue, Fri: "IF THE MAP WAS DRAWN BY…" — Natural Earth cartogram morph (population, GDP, coffee, internet users…),
  like render/prompts/taqqos_xarita.md but world/regional and English.
- Wed, Sat, Sun: "5 FACTS THAT SOUND FAKE" — like render/prompts/taqqos_bilasizmi_v2.md (progress 01/05, motion
  graphics over licensed real photos/maps, last fact strangest, loop). Strange borders, places, records, money.
Never repeat a topic/pair: Drive Google Doc "OUJ EN log" (create if missing).

## MOTION & GRAPHICS — exactly the Taqqos level (owner 20 Nov: "Taqqos'dagidek elementlar, animatsiya, grafiklar")
Every second something moves. Use these templates (working code, Pillow+numpy, 1080x1920):
- render/templates/five_facts_diomid.py — globe zoom (Natural Earth), progress bar 01/05, counters, ruler, clock cards,
  date-line draw, panels, loop to frame 1; render/templates/five_facts_warp_to_voice.py — retime frames to narration.
- render/templates/xarita_cartogram.py — cartogram morph by data with labels and number cards.
- "Who's stronger?": the newest Taqqos taqqosNN.py on branch media (tools/taqqos/) — flags fly in with bounce + flash +
  camera shake, counters count up, race bars grow, winner glow + "+1", live scoreboard flip, confetti winner card.
Required in every video: animated counters (never static numbers), at least one chart/bar/map that draws itself,
flags or maps drawn accurately, smooth eased transitions (no hard static cuts), word-synced big captions, loop ending.
Preview ≥ 6 frames before rendering and fix anything static.

## Build
22–35 s, 1080x1920, 30 fps; dark navy + gold accent; first frame = shocking claim + motion; text never in the bottom 18 %.
Every number from 2 reliable sources (World Bank, IMF, UN, CIA Factbook, NASA/USGS, Britannica) with the year; no invented
numbers. Licensed media only (Wikimedia Commons with credit, NASA/USGS PD, Natural Earth). Free Z7 Render or local
Pillow/ffmpeg (see GUIDE / the Taqqos briefs). Voice (owner 20 Nov: FREE voice): Kokoro via the same method as render/prompts/ouj_daily.md, English MALE voice
`#voice=am_michael speed=1.0` (keep the same voice every day). Only if Kokoro fails twice: ElevenLabs (connector "ElevenLabs-ee62b10f" or fallback "ElevenLabs"),
one calm-confident English male voice chosen once via creative_list_voices (languages ["en"]) — record its voice_id in the
Drive log and reuse it; eleven_v3, generations_count 1. Music bed generated in code, ducked under voice, −14 LUFS.
QA ≥ 6 frames: numbers = narration = sources, readable, loop.

## Post & report
Metricool brand 7697106, providers [{"network":"youtube"}] ONLY (this brand's Instagram is B2B — never post there),
type "short", public, madeForKids false, category EDUCATION, isAiGeneratedContent true.
POSTING TIME (owner 20 Nov: US evening): 19:00 America/New_York of the same US calendar day = 05:00 Asia/Tashkent the
NEXT morning. Use publicationDate {"dateTime":"<YYYY-MM-DD>T19:00:00","timezone":"America/New_York"}. Guard against
duplicates by checking that US date (America/New_York) for an existing YouTube post on brand 7697106. Title: hook + #shorts + 2 hashtags
(e.g. "Japan vs Germany: who's really stronger? ⚔️ #shorts #japan #germany"). Description: hook line, question
("Which one would you pick? 👇"), Sources (URLs + year), Image credits, "Voice: AI-generated.", ≤5 hashtags.
Pinned comment idea in the log. Report one short Uzbek line: select public.z7_tg('8355820653','message','🌍 OUJ (EN): <mavzu> — <HH:MM>');
