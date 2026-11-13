# OUJ daily Short — production + posting (executor instructions, 13 Nov 2026)
Owner reads short Uzbek (Latin). Times for him in Tashkent time (UTC+5). Posting times below are Europe/Moscow.
Channel: OUJ_Official (@ouj_n1, YouTube UCRnmG4C7n5eH2u0lK5vPflw), English, US/EU audience. Promise: "Is this place even real?"
MONEY: only free tools — Kokoro voice + "Z7 Render" (GitHub Actions). Never vidIQ/Kling/VideoDB/invideo paid generation.

1. TOPIC (Mon–Sat): ONE real place that looks unreal (e.g. Salar de Uyuni, Zhangye, Lake Hillier, Socotra, Fly Geyser,
   Vinicunca, Pamukkale, Lençóis Maranhenses, Waitomo, Spotted Lake, Marble Caves, Tianzi, Antelope Canyon, Plitvice…).
   Never repeat a place within 60 days: check Google Drive "OUJ log | …" files AND `ls render/jobs/ouj_*` on branch render
   (13 Nov = Cappadocia). Needs ≥5 Pexels clips whose page title names the place (WebSearch allowed_domains ["pexels.com"]).
   Sunday = game Short (5 labelled clips "1"…"5", "Guess the country", answers in pinned comment), no voice.
2. FACTS: 3 verified facts (Wikipedia + sources, UNESCO, official sites). Never invent numbers.
3. VOICE (free): narration 75–90 words, starts with a question without naming the place, numbers as words, ends
   "Would you go? Which country should we show next?". Clone branch fetch-media, write fetch/tts/jobs/ouj_<YYYYMMDD>.txt
   (first line `#voice=af_heart speed=0.95`), commit+push; wait (git pull every 30 s, max 20 min) for
   fetch/out/tts/ouj_<YYYYMMDD>.mp3 + .json (word timings {w,s,e}).
4. RENDER: follow render/GUIDE.md. Example job: render/jobs/ouj_20261113_cappadocia.json (copy its structure):
   6–8 Pexels scenes `https://www.pexels.com/download/video/<ID>/` 4–5 s, hook (2–4 words, vary colour), texts for
   place name + 3 facts + CTA (pos 0.30, ≤7 words, NO emoji in on-screen text), captions karaoke with the json word timings
   (+0.2 s voice offset), music b2b_beat_0<N>.mp3 (N = day % 6 + 1) volume 0.12 duck. Copy the mp3 into
   render/assets/<job>/voice.mp3. Push to branch render, wait for render/out/<name>.json (ok → url).
   QA: extract 5 frames with ffmpeg and look at them.
5. POST: Metricool createScheduledPost blogId "7697106", providers [{"network":"youtube"}] ONLY, media [render url],
   publicationDate today 19:00 Europe/Moscow (now+15 min if past), autoPublish true, youtubeData {title ≤100 chars with
   #shorts + 2 relevant hashtags, type "short", privacy "public", tags, category "TRAVEL_EVENTS", madeForKids false,
   isAiGeneratedContent false}. Description: hook, 3 facts, "Which country should we show next? 👇", Sources,
   "Footage: Pexels", "Narration: AI voice". If Metricool fails, report the exact error.
6. TELEGRAM (allowed chats only): OUJ channel "-1004456004836": the video (make ≤20 MB copy: ffmpeg -crf 30, host on
   fetch-media fetch/out/) + one message with TITLE / DESCRIPTION / TAGS / PINNED COMMENT in <code>; one short Uzbek line to
   "8355820653". Method: Supabase execute_sql net.http_post to https://mia-z7.app.n8n.cloud/webhook/z7-telegram-send
   ({chat_id, kind message|video, text | file_url+caption}); if Supabase is unavailable use branch tg-outbox
   (tg/<date>_ouj_<n>.json files, json.dump ensure_ascii=False).
7. LOG: Google Drive "OUJ log | <YYYY-MM-DD> | <place> | finished" with facts+sources, clips, RENDER URL, texts, Metricool id.
If something fails twice: send one short Uzbek line with the exact error to 8355820653 and stop. Never post a broken video.
