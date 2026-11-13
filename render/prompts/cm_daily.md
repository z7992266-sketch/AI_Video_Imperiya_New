# CineMatrix daily Short — production (executor instructions, 13 Nov 2026)
Owner reads short Uzbek (Latin); times for him in Tashkent time. Channel CineMatrix (YouTube @CineMatrix_AI, brand 7653061),
Russian, format "Секреты мест": 35–50 s mini-documentary about a real place/structure with a record or secret.
1. TOPIC: CIS-relevant (Uzbekistan / Central Asia / Russia) secret or record places. Skip topics already done: check Drive
   "CineMatrix log | …" and `ls render/jobs/cm_*` on branch render (done: Ташкентское метро, Чернобыль саркофаг 11 Nov,
   Кольская скважина 13 Nov). Ideas: землетрясение 1966 Ташкент, Мурунтау, Аральское море, Ташкентская телебашня, Байконур,
   Чарвак, Регистан, Метро-2, Бурдж-Халифа фундамент.
2. FACTS verified with WebSearch/WebFetch; legends always marked "не подтверждается". Sources in the description.
3. VOICE: ElevenLabs connector "ElevenLabs-ee62b10f" creative_generate_speech, voice Alex Bell TUQNWEvVPBLzMBSVDPUA,
   eleven_v4, generations_count 1; copy the audio into render/assets/<job>/voice.mp3 via branch fetch-media.
   If ElevenLabs is unavailable: free Piper voice — fetch/tts/jobs/cm_<YYYYMMDD>.txt with first line `#voice=ru_dmitri speed=1.0`
   (output fetch/out/tts/cm_<YYYYMMDD>.mp3). Narration 90–110 words, numbers as words.
4. VISUALS: 7–10 licensed photos/clips (Wikimedia Commons PD/CC, Pexels, NASA). Get direct upload.wikimedia.org URLs and
   author/licence via the Commons API (put the API URL into fetch-media fetch/urls.txt if the sandbox blocks it).
   Max 2 AI stills (ElevenLabs creative_generate_image) only for cross-sections, with "AI-реконструкция" text while shown.
5. RENDER: render/GUIDE.md; example job render/jobs/cm_20261113_kola.json (hook = big number, texts for numbers/years,
   captions karaoke ru, music gen "dark"/"tension", grade "cinematic"/"dark"). Wait for render/out/<name>.json, QA 5 frames.
6. LOG (before 13:00 MSK — the 13:13 posting task reads it): Google Drive "CineMatrix log | <YYYY-MM-DD> | <topic> | finished"
   with labelled lines: "RENDER URL: <url>", "vidIQ uploadId: none — free render", "YT TITLE: …" (≤70 chars + #shorts),
   "YT DESCRIPTION: …" (facts, Источники, Фото credits, "Озвучка — AI"), "YT TAGS: …", "IG CAPTION: …" (max 5 hashtags),
   "PINNED COMMENT: …".
7. TELEGRAM: CineMatrix channel "-1004379758095": video (≤20 MB copy) + posting pack; one short Uzbek line to 8355820653.
   Method as in render/prompts/ouj_daily.md step 6.
If something fails twice: report the exact error to 8355820653 and stop.
