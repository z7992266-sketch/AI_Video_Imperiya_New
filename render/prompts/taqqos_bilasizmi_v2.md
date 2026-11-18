# TAQQOS "BILASIZMI" v2 — production brief (owner, 18 Nov 2026)

Owner: "bulut ko'rinishini olib tashla, Bilasizmi'dan boshqacha — grafikli, rasmlari bilan, animatsiyalar qo'shish kerak"
(views fell to 20–60). The old cloud template (render/bilasizmi.py clouds, ?/! bubbles) is RETIRED — never use it.
Also obey render/prompts/taqqos_growth.md. NO WHOOSH, no boom. Owner reads short Uzbek (Latin), times in Tashkent.

## Format: "5 ta fakt" (22–30 s, vertical 1080x1920, 30 fps)
- FRAME 1 (0–1.2 s): no word "Bilasizmi". The single most shocking visual of the topic full-screen + a huge 3–5-word
  headline (e.g. "BU OROLDA HALI KECHA"), motion from frame 1 (zoom/pan). Small chip: "5-chisi eng g'alati".
- Top progress UI for the whole video: thin gold bar filling up + "01 / 05" counter + topic label (left).
- Each fact ≈ 4–5 s and ALWAYS has motion graphics, not just a photo:
  * full-screen real photo/satellite with Ken Burns + a graphic layer on top: animated number counter, bar/line chart
    drawing itself, map with glowing outline + pin/route line, distance ruler, clock/date cards, comparison bars.
  * one short on-screen line (≤ 7 words), big, bottom-third but above the bottom 18 % safe zone.
  * small source chip under it (e.g. "NASA", "US Census 2020").
- Last fact = the strangest one; final 2 s: debate question card ("Siz qaysi biriga ishonmadingiz? Izohda yozing")
  then cut back to frame 1 composition (loop).
- Style: dark navy/black + gold accent (#E9B949) + one topic colour; Inter / our fonts; no clouds, no cartoon bubbles,
  no emoji stickers, no AI images of real people or places pretending to be real photos.
- You may reuse globe/map code: Natural Earth (public domain) via `git clone --depth 1 --filter=blob:none --sparse
  https://github.com/nvkelso/natural-earth-vector.git` (sparse geojson), orthographic globe zoom like Abdufattoh/Xarita.

## Topics (never repeat — Drive Doc "Taqqos Bilasizmi log")
Strange places & borders, money/prices around the world, records, Uzbekistan facts few know, space/nature numbers.
NOT health/medicine, NOT religion, NOT politics opinions. Queue start:
1. Diomid orollari (Rossiya–AQSh, 3,8 km, sana chizig'i, qishda 21 soat farq; muz ko'prigi bo'ladi, lekin chegarani
   kesib o'tish taqiqlangan; Kichik Diomidda ~80 kishi yashaydi — US Census 2020; Katta Diomidda doimiy aholi yo'q).
2. Baarle-Nassau / Baarle-Hertog (chegara uylar ichidan o'tadi). 3. Dunyodagi eng yaqin ikki poytaxt (Kinshasa–Brazzavil).
4. Point Roberts (AQSh, faqat Kanada orqali). 5. Llívia (Ispaniya anklavi Fransiyada).
Every number verified with 2 reliable sources; state the year; no invented numbers; legends labelled.

## Voice, assets, render
- Narration Uzbek (Latin) 60–85 words, fast and lively, numbers as words, ends with the question.
  ElevenLabs "ElevenLabs-ee62b10f", voice_id 269BA7xEbcFPbGfqUFwe, model eleven_v3, generations_count 1;
  creative_transcribe_audio for word timings; sync each fact + graphic to the words.
- Photos: Wikimedia Commons (PD/CC0/CC BY/CC BY-SA, record author+licence) or NASA/USGS/ESA public domain,
  fetched via the fetch-media branch (upload.wikimedia.org .../960px-... thumbs work).
- Build frames yourself with Python (Pillow/numpy/matplotlib) → silent mp4 → fetch-media → render job
  render/jobs/taqqos_bil2_<YYYYMMDD>_<slug>.json (one video scene, voice, low music gen "calm"/"tension", sfx:false,
  captions style none) OR mix locally with ffmpeg (voice + low music, loudnorm -14 LUFS) and host on fetch-media.
- QA: look at ≥ 6 frames (frame 1, each fact, question card, last frame): text readable, inside safe zone, numbers =
  narration = sources, no clouds, graphics actually moving. ffprobe has audio.

## Post & report
Metricool brand 7705124, YouTube Short, 19:00 Asia/Tashkent (17:00 Europe/Moscow) of the run day (if past, next free
15-min slot ≥ 1 h from other Taqqos posts). Title: hook only, no "Bilasizmi?" prefix, e.g.
"Bu orolda hali kecha… 🤯 #shorts #taqqos #faktlar". category EDUCATION, madeForKids false, isAiGeneratedContent true.
Description: 2-line hook, "Siz qaysi biriga ishonmadingiz? Izohda yozing! 👇", "Manbalar:" (URLs), "Rasmlar:"
(file — author, licence), "Ovoz sun'iy intellekt (AI, ElevenLabs) yordamida yaratilgan.", max 5 hashtags.
Log to Drive "Taqqos Bilasizmi log"; one short Uzbek line to 8355820653 via the usual Telegram method (if every
method fails, put it in the final reply). Never post a broken video.
