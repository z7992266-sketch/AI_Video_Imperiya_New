# TAQQOS LONG VIDEO — twice a week (Wed + Sun, 18:00 Asia/Tashkent)

Owner (14 Nov 2026): "haftada 2 ta long", "faktlar, rasm va animatsiyalar juda qiziq bo'lishi kerak; vjuuv degan ovoz kerak emas".
Owner reads short Uzbek (Latin). Decide everything yourself, ask nothing. Times for the owner in Tashkent time.

## Guard
If today (Asia/Tashkent) is 2026-11-15, STOP and do nothing: that day's long (O'zbekiston va Rossiya) is produced by a separate manual run. Also stop if Metricool brand 7705124 already has a long YouTube video (type "video") scheduled or published today.

## Channel
Taqqos — YouTube @Taqqos_Uzb (UCjxj5-qg5FV5GOb5Li5PiaA), Metricool brand 7705124, Uzbek Latin.
Data (Nov 2026): Shorts "O'zbekiston vs Rossiya / Xitoy / Hindiston / Yaponiya" get 70k–260k views; the long "Orol dengizi 1964 vs 2026" kept viewers 3:10 on average. Goal of every long: average view duration ≥ 4 min (monetisation needs watch hours).

## Topic queue (take the first one NOT in Drive "Taqqos long log" files; then invent new ones of the same kind)
1. O'zbekiston va Rossiya: 10 ta raqamda to'liq taqqos  (planned 15 Nov 2026)
2. O'zbekiston va Xitoy: 10 ta raqamda
3. O'zbekiston va Hindiston: 10 ta raqamda
4. 1991 va bugun: O'zbekiston 35 yilda qanday o'zgardi (satellite images, maps)
5. O'zbekiston va Yaponiya: kim qanday yashaydi (ish haqi, uy, umr, transport)
6. Toshkent 1966 zilzilasi: shahar qanday qayta tug'ildi (archive photos, PD/CC only)
7. O'zbekistonning 10 ta rekordi va noyob joyi
8. O'zbekiston va Turkiya: 10 ta raqamda
9. O'zbekiston va Germaniya: 10 ta raqamda
10. Agar O'zbekistonda dengiz bo'lganida… (map "what if", clearly labelled as a thought experiment)
11. O'zbekiston va Qozog'iston: 10 ta raqamda
12. Buyuk Ipak yo'li: 2000 yil oldin va bugun

## Facts
Every number verified with 2 reliable sources (World Bank, IMF, UN, stat.uz, official national statistics, Britannica, UNESCO, IOC, UNWTO, NASA). State the year. No invented numbers; legends labelled. Neutral and respectful to every country; no politics, no religion, no leaders' faces. Never use the words "raund" or "jang" (use "1-taqqos", "bo'lim").

## Make it gripping (mandatory)
- 8–12 min, 16:9 1920x1080, 30 fps.
- Hook 0–5 s: the most surprising number of the video + big animated text, motion from frame 1; promise "eng hayratlanarlisi oxirida".
- A new visual every 30–40 s: animated maps (both countries highlighted, to-scale overlays), counting-up numbers, animated bar/race charts, icons, split-screen photos, timelines.
- Scoreboard (e.g. "O'zbekiston 3 — 2 Rossiya") updated after each area for country comparisons; question cards "Sizningcha qaysi biri ko'proq?" with a 2-s pause, then the reveal; final result only at the end.
- 40+ licensed visuals (Wikimedia Commons CC0/PD/CC BY/CC BY-SA with author+licence, NASA/ESA PD, Pexels). No AI images of real people, no logos, no other creators' footage. No image longer than ~6 s, varied Ken Burns.
- Chapters with timestamps; 8-s end screen.

## Sound
Uzbek narration: ElevenLabs connector "ElevenLabs-ee62b10f", voice_id 269BA7xEbcFPbGfqUFwe, eleven_v3 (fallback eleven_multilingual_v2), chunks ≤ 2,500 chars, generations_count 1; check credits first (≤ 12,000 per video; if the plan is low, shorten to 7–8 min). Never name the voice publicly. Soft generated music bed, ducked. ABSOLUTELY NO WHOOSH (render.py has whoosh off by default; never add whoosh sfx_events). ≈ -14 LUFS, true peak ≤ -1 dB.

## Build
Reuse and upgrade the previous long-video pipeline: look at branch media taqqos/long/*.mp4 (orol_v1, founders_v1) and any build code/logs, the kit on branch kit-glitchverse (glitch/build.py = 16:9 documentary renderer with maps, cards, Ken Burns, credits) and render/render.py. Heavy renders can run in GitHub Actions on your own work branch. Use fetch-media to download files the sandbox proxy blocks.
QA: extract ≥ 20 frames and LOOK at them (readable text, no overlap, no black frames, credits visible); check audio sync at 3 points. Thumbnail 1280x720: flags/visual, big number or "?", 2–4 words, high contrast.

## Host + post
Re-encode < 95 MB, push to fetch-media fetch/out/taqqos_long_<slug>_<YYYYMMDD>.mp4 (+ _thumb.jpg). Metricool getScheduledPosts 7705124 (no duplicates), createScheduledPost blogId 7705124 at 18:00 Asia/Tashkent the same day (16:00 Europe/Moscow; if past, next free 15-min slot), youtube type "video", privacy public, category EDUCATION, madeForKids false, isAiGeneratedContent false, videoThumbnailUrl = thumb raw URL (retry without it if rejected). Title ≤ 100 chars hook-style. Description: hook line, chapters with timestamps, debate question, "Manbalar:", "Rasmlar:" credits, "Ovoz sun'iy intellekt (AI) yordamida yaratilgan.", ≤ 5 hashtags. Pinned comment = debate question. Also cut 2 vertical teaser clips (20–40 s) from the long with "To'liq video kanalda 👆" and schedule them as Shorts on the next two days at 12:00 Tashkent (only if no other Short is within 1 hour).

## Report
Drive "Taqqos long log | <YYYY-MM-DD> | <topic> | scheduled" (script, sources, credits, URLs, Metricool ids, ElevenLabs credits). One short Uzbek Telegram message to 8355820653 (topic, 18:00, pinned comment in <code>) via Supabase execute_sql net.http_post to https://mia-z7.app.n8n.cloud/webhook/z7-telegram-send (fallback: tg-outbox branch file). If something fails and cannot be fixed, never post a broken video — say what failed in one line.
