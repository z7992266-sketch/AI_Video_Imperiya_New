> TELEGRAM (19 Nov 2026): use `select public.z7_tg(chat_id, kind, text, file_url, caption);` via Supabase execute_sql (project vtsurdinopzycwsfzsuk) — the n8n relay below is dead. See render/GUIDE.md top.

> **VOICE RULE (owner, 25 Nov 2026) — overrides everything below:** every Taqqos long uses ONLY the ElevenLabs voice 269BA7xEbcFPbGfqUFwe (eleven_v3). NEVER use Edge TTS / uz_tts.py / any other voice. Check credits first (account_get_usage): if remaining credits are below what the script needs, DO NOT render with another voice — write the script, save it to render/jobs, skip publishing, and tell the owner in bot chat 8355820653 (short Uzbek) that the video waits for the ElevenLabs credit reset.

# TAQQOS LONG VIDEO — twice a week (Wed + Sun, 18:00 Asia/Tashkent)

Owner (14 Nov 2026): "haftada 2 ta long", "faktlar, rasm va animatsiyalar juda qiziq bo'lishi kerak; vjuuv degan ovoz kerak emas".
Owner reads short Uzbek (Latin). Decide everything yourself, ask nothing. Times for the owner in Tashkent time.

## Guard
If today (Asia/Tashkent) is 2026-11-15, STOP and do nothing: that day's long (O'zbekiston va Rossiya) is produced by a separate manual run. Also stop if Metricool brand 7705124 already has a long YouTube video (type "video") scheduled or published today.

## Channel
Taqqos — YouTube @Taqqos_Uzb (UCjxj5-qg5FV5GOb5Li5PiaA), Metricool brand 7705124, Uzbek Latin.
Data (Nov 2026): Shorts "O'zbekiston vs Rossiya / Xitoy / Hindiston / Yaponiya" get 70k–260k views; the long "Orol dengizi 1964 vs 2026" kept viewers 3:10 on average. Goal of every long: average view duration ≥ 4 min (monetisation needs watch hours).

## Topic queue (owner 27 Nov 2026 — take the first one NOT in Drive "Taqqos long log"; at most 1 football long in every 3; then invent new ones of the same kind)
1. Makka raqamlarda: Masjid al-Haram 1400 yilda qanday kengaydi va bir yilda necha million kishi keladi
2. Madina: Masjid an-Nabaviy — kichik masjiddan dunyodagi eng katta masjidlardan biriga
3. Masjid al-Aqso va Qubbat as-Sahro: Quddus eski shahridagi 1300 yillik tarix va me'morchilik
4. Futbol: O'zbekiston terma jamoasi tarixi — 1992 dan Jahon chempionati 2026 gacha raqamlarda
5. Dunyoni o'zgartirgan 5 ta allomamiz: Al-Xorazmiy, Ibn Sino, Beruniy, Ulug'bek, Imom Buxoriy
6. Ka'ba haqida 10 ta kam odam biladigan fakt (kiswa, qora tosh, qurilish tarixi)
7. Samarqand, Buxoro, Xiva: Ipak yo'li shaharlari 1000 yil oldin va bugun
8. Futbol: Superliga tarixi — eng ko'p chempion, eng katta g'alabalar, rekordlar
9. Dunyodagi eng katta 10 ta masjid (sig'imi, maydoni, yili)
10. O'zbekiston va Saudiya Arabistoni: 10 ta raqamda
11. Hajj: 1950-yildan bugungacha — ziyoratchilar soni, transport, xavfsizlik
12. Old queue (still allowed): O'zbekiston va Xitoy / Hindiston / Yaponiya / Turkiya / Qozog'iston, 1991 va bugun, Toshkent 1966 zilzilasi, Buyuk Ipak yo'li

## Sacred places & religion rules (mandatory for topics 1–3, 5, 6, 9, 11)
- Respectful, calm tone; facts, history, architecture, numbers only. No fiqh rulings, no sect/madhhab comparisons, no preaching, no jokes.
- NEVER depict prophets, companions or angels in any form (no drawings, silhouettes, AI images). No AI images of the holy places presented as real — use licensed photos (Wikimedia Commons CC/PD with author+licence), our own maps, diagrams, timelines and 3D-style expansion graphics.
- Masjid al-Aqso: history and architecture only (Umayyad building, Qubbat as-Sahro 691–692 y., later restorations). Location = "Quddus (Jerusalem) eski shahri". No politics, no conflict footage or casualty imagery, no statements about sovereignty or borders.
- Numbers (Hajj pilgrims, mosque capacity/area, expansion years) from ≥2 sources: Saudi General Authority for Statistics (stats.gov.sa), Saudi Ministry of Hajj, Britannica, UNESCO, academic/encyclopedic sources; state the year; if sources disagree, say "taxminan" and give the range.
- Islamic terms spelled the usual Uzbek way (Makka, Madina, Ka'ba, Masjid al-Haram, Masjid an-Nabaviy, Hajj, Umra). Quran verses only if quoted exactly with sura:oyat; otherwise none.
- Music: in these videos no music at all — voice + soft ambient only (respect for the audience).

## Facts
Every number verified with 2 reliable sources (World Bank, IMF, UN, stat.uz, official national statistics, Britannica, UNESCO, IOC, UNWTO, NASA). State the year. No invented numbers; legends labelled. Neutral and respectful to every country; no politics, no leaders' faces; religion only as history/heritage under the sacred-places rules above. Never use the words "raund" or "jang" (use "1-taqqos", "bo'lim").

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
25 Nov 2026 pipeline (Navbahor finalda, 8:43): render/templates/taqqos_long_build.py (PIL frames: scoreboards, match timelines, road/bracket, stat cards, bars, trophies; captions from word timings). NOTE: that run used Edge TTS (SardorNeural) because ElevenLabs credits were low — the owner rejected it (25 Nov: "diktor ovozi nega boshqa, talaffuzi chotkiy emas, bir xil chiqsin").
Reuse and upgrade the previous long-video pipeline: look at branch media taqqos/long/*.mp4 (orol_v1, founders_v1) and any build code/logs, the kit on branch kit-glitchverse (glitch/build.py = 16:9 documentary renderer with maps, cards, Ken Burns, credits) and render/render.py. Heavy renders can run in GitHub Actions on your own work branch. Use fetch-media to download files the sandbox proxy blocks.
QA: extract ≥ 20 frames and LOOK at them (readable text, no overlap, no black frames, credits visible); check audio sync at 3 points. Thumbnail 1280x720: flags/visual, big number or "?", 2–4 words, high contrast.

## Host + post
Re-encode < 95 MB, push to fetch-media fetch/out/taqqos_long_<slug>_<YYYYMMDD>.mp4 (+ _thumb.jpg). Metricool getScheduledPosts 7705124 (no duplicates), createScheduledPost blogId 7705124 at 18:00 Asia/Tashkent the same day (16:00 Europe/Moscow; if past, next free 15-min slot), youtube type "video", privacy public, category EDUCATION, madeForKids false, isAiGeneratedContent false, videoThumbnailUrl = thumb raw URL (retry without it if rejected). Title ≤ 100 chars hook-style. Description: hook line, chapters with timestamps, debate question, "Manbalar:", "Rasmlar:" credits, "Ovoz sun'iy intellekt (AI) yordamida yaratilgan.", ≤ 5 hashtags. Pinned comment = debate question. Also cut 2 vertical teaser clips (20–40 s) from the long with "To'liq video kanalda 👆" and schedule them as Shorts on the next two days at 12:00 Tashkent (only if no other Short is within 1 hour).

## Report
Drive "Taqqos long log | <YYYY-MM-DD> | <topic> | scheduled" (script, sources, credits, URLs, Metricool ids, ElevenLabs credits). One short Uzbek Telegram message to 8355820653 (topic, 18:00, pinned comment in <code>) via Supabase execute_sql net.http_post to https://mia-z7.app.n8n.cloud/webhook/z7-telegram-send (fallback: tg-outbox branch file). If something fails and cannot be fixed, never post a broken video — say what failed in one line.
