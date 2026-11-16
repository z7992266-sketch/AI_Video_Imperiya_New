# TAQQOS "XARITA" SHORT — production brief (owner approved 16 Nov 2026)

Owner (16 Nov 2026): "shunaqa qiziq taqqoslashni ham yo'lga qo'yishimiz kerak, taqqos tushib ketyapti, prosmotr kuchaytirishimiz kerak".
Format idea: a map that REDRAWS itself by data ("Xarita aholiga qarab chizilsa-chi?") — regions/countries grow or shrink
to their share of population / money / births etc. People find their own region and share it. This is a general
data-visualisation technique (cartogram). NEVER copy another creator's video, design, title wording, colours, logo or
music (e.g. @birfoiz_ made a similar video — do not imitate its look; build our own Taqqos style).

Owner reads short Uzbek (Latin). Decide yourself, ask nothing. Times for the owner in Tashkent time.
Also obey render/prompts/taqqos_growth.md (no repeats, hook, variety, loop, NO WHOOSH).

## 0. Guard
- Today = Asia/Tashkent date. Metricool getScheduledPosts brand 7705124 for the publish day: if a post whose title
  contains "Xarita" is already scheduled/published that day → stop, do nothing.
- Publish slot: 18:00 Asia/Tashkent (= 16:00 Europe/Moscow) on the publish day given in the run text (default: today;
  if 18:00 already passed, next free 15-min slot ≥ 1 h away from other Taqqos posts that day).

## 1. Topic (never repeat — read Drive Google Doc "Taqqos Xarita log", create it if missing)
Queue (take the first unused; each needs 2 reliable sources + year):
1. "Markaziy Osiyo xaritasi aholiga qarab chizilsa" — 5 countries (+ optional Afg'oniston): area vs population.
   Hook: Qozog'iston ~6× bigger than O'zbekiston on the real map, but O'zbekiston has more people. (Verify with
   World Bank / UN WPP / national stat offices, give year.)
2. "Dunyo xaritasi aholiga qarab" — continents or top ~30 countries; Hindiston/Xitoy swell, Rossiya/Kanada shrink.
3. "Dunyo xaritasi boylikka (YaIM) qarab" — World Bank / IMF, current USD, year.
4. "O'zbekiston viloyatlari: o'rtacha oylik bo'yicha" — stat.uz official, latest period.
5. "Viloyatlar: tug'ilish soni bo'yicha" — stat.uz.
6. "Viloyatlar: xorijiy turistlar bo'yicha" — official tourism committee / stat.uz.
7. "Markaziy Osiyo: internet tezligi" — Ookla Speedtest Global Index (month, year).
8. "Dunyo: futbol bo'yicha" — FIFA ranking points (date).
Avoid repeating the exact metric pair of the reference video (viloyatlar yer vs aholi) — pick different metrics.
Strictly neutral: no politics, no ethnic/regional mockery, no "eng yomon viloyat" style shaming; positive curiosity.

## 2. Data & boundaries (licensed only)
- Boundaries: Natural Earth (public domain) via GitHub `nvkelso/natural-earth-vector` (geojson/ne_50m_admin_0_countries.geojson)
  and for Uzbek regions geoBoundaries (CC BY 4.0) via GitHub `wmgeolab/geoBoundaries` (UZB ADM1). Download through
  raw.githubusercontent.com / github.com (allowed) or the fetch-media workflow. Credit: "Chegaralar: Natural Earth;
  geoBoundaries (CC BY 4.0)". Do NOT use GADM (non-commercial).
- Numbers: official stats only (stat.uz, World Bank, UN, IMF, Ookla, FIFA). Write the source + year ON SCREEN
  (small line under the title) and in the description.

## 3. Visual (our own style — Taqqos dark navy + our accent colours, our fonts in render/fonts)
Build frames locally with Python (pip install --break-system-packages geopandas shapely matplotlib pillow numpy):
- 1080x1920, 30 fps, ~24–30 s. Frame 1 = the real map already moving (slow zoom) + huge 2–4 word question title.
- Morph: each region is scaled about its centroid by sqrt(value_share / area_share) (non-contiguous cartogram;
  honest and readable), animated over ~1.5 s with ease-in-out; labels "Name  NN,N %" pop in on the big movers.
- Bottom info card (above the bottom 18 % safe zone): region name + two bars ("YER" vs "ODAM" / chosen metric).
- Sequence: real map → metric morph → highlight the top 3 + biggest surprise → back to the real map (LOOP:
  last frame == first frame).
- Change ≥ 2 visual elements vs the previous Xarita video (palette, background motion, card style, font accent).
- Write frames → ffmpeg (libx264, yuv420p, crf 20) → mp4 without audio.

## 4. Voice & sound
- Uzbek (Latin) narration 55–80 words, numbers as words, starts with the hook question, ends with:
  "Sizning viloyatingiz (davlatingiz) nechanchi o'rinda? Izohda yozing!"
- ElevenLabs connector "ElevenLabs-ee62b10f", voice_id 269BA7xEbcFPbGfqUFwe, model eleven_v3, generations_count 1;
  creative_transcribe_audio for word timings (align the morphs to the words). Never say the voice name publicly.
- Download audio via the fetch-media branch. Music: render.py gen "calm" or "tension" low (0.12, duck).
  SFX: only very soft "tick"/"pop" on label pops. NO WHOOSH, no boom (owner 14 Nov).

## 5. Render
Pre-rendered video + narration pattern from render/GUIDE.md: commit the silent mp4 to fetch-media
(fetch/out/xarita_<YYYYMMDD>_<slug>.mp4), then render job render/jobs/taqqos_xarita_<YYYYMMDD>_<slug>.json with
one scene {"type":"video","native_audio":false,"move":"none","grade":"none"}, "voice", "music", "captions":{"style":"none"},
"transition":"none","sfx":false. Wait for render/out/<name>.json.

## 6. QA (must pass before posting)
Extract 6 frames (0.3 s, each morph, info card, last frame) and LOOK: numbers on screen = narration = sources;
labels readable, nothing in the bottom 18 %, no overlapping labels, map not distorted wrongly, source line visible,
first and last frame match. ffprobe shows audio. Fix and re-render if anything is off.

## 7. Post (Metricool brand 7705124, YouTube Short)
createScheduledPost: publicationDate <publish day>T16:00:00 Europe/Moscow (= 18:00 Tashkent), providers youtube,
youtubeData {type "short", privacy "public", category "EDUCATION", madeForKids false, isAiGeneratedContent true,
title ≤ 100 chars curiosity style e.g. "Xaritani aholiga qarab chizsak… O'zbekiston kattalashdi 🤯 #shorts #xarita #taqqos"}.
Description: 2 lines hook, "Sizning viloyatingiz nechanchi? Izohda yozing 👇", "Manbalar:" (URLs + year),
"Chegaralar: Natural Earth; geoBoundaries (CC BY 4.0)", "Ovoz sun'iy intellekt (AI, ElevenLabs) yordamida yaratilgan.",
max 5 hashtags. Pinned-comment text = the debate question (put it in the log for the pin digest).

## 8. Report
Drive Doc "Taqqos Xarita log": date | topic | metric | sources | palette/style | render URL | Metricool id | pinned comment.
One short Uzbek line to chat 8355820653 ("🗺 Taqqos Xarita: <mavzu> — <kun> 18:00 da chiqadi") via the usual
Telegram method; if every Telegram method fails, put it in the final reply. Never post anything broken.
