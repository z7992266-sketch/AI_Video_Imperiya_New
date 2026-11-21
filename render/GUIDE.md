# Z7 Render — guide for the daily channel tasks

> **TAQQOS = FUTBOL (owner, 21 Nov 2026: "eski usulimizni futbolga o'zgartir") — WINS over the topic lists in every
> render/prompts/taqqos_*.md and every Taqqos task prompt. Keep each format's look, motion, voice, timing and posting slot;
> only the SUBJECT becomes football:** "Kim kuchli?" → player vs player / club vs club / national team vs national team in
> numbers (goals, assists, trophies, Ballon d'Or, transfer fees, attendance); "Xarita" → football maps (where World Cup /
> Ballon d'Or winners come from, biggest stadiums per country, where Uzbekistan's players play); "Grafik" → self-drawing
> stat charts (goals per season, transfer record over time, World Cup goals per tournament); "5 ta fakt" → 5 surprising
> football facts; "Tarix" → football history stories; Taqqos long → 8–12 min football rankings / history ("Futbol tarixidagi
> 10 ta eng …").
> FOCUS (owner 21 Nov): mostly O'ZBEKISTON — terma jamoa (Jahon chempionati 2026, Osiyo kubogi, o'yinchilar), Superliga
> klublari, ESPECIALLY Farg'ona vodiysi jamoalari: Navbahor (Namangan), Andijon, Neftchi (Farg'ona) — plus Pakhtakor,
> Nasaf, Paxtakor derbilari, o'zbek futbolchilari xorijda. World stars (Messi/Ronaldo…) at most 1 in 4 videos.
> NEWS FORMAT "SUPERLIGA: N-TUR YAKUNLARI" (owner 21 Nov: "kechagi Navbahor–Neftchi o'yini, Paxtakor o'yini, Nasaf jadvalda
> tushib ketdi — shunaqa qiziq faktlar"): after each Superliga round (or a big terma jamoa match) a 40–55 s Short — scores as
> a scoreboard, 1–2 key moments in words (goals, red cards, comebacks), animated table showing who moved up/down (arrows),
> one surprising number. Results/table from ≥2 Uzbek sports sites (aniq.uz, zamin.uz, tribuna.uz, kun.uz, daryo.uz, pfl.uz)
> checked on the day; never guess a score. No match video — our own scoreboard/table graphics only.
> Club facts (founded year, titles, stadium capacity, top scorers) need ≥2 sources (PFL.uz / club site / Wikipedia / Transfermarkt). Sog'liq "30 kun" series stays health (unchanged).
> RULES: stats from ≥2 sources with the date ("2026-yil noyabr holatiga"); never match footage, TV broadcast clips, club /
> league / FIFA logos or kits with crests, never AI-generated real players. Visuals = our own graphics (generic numbered
> shirts in team colours, bars, counters, pitch, trophies, maps) + optional Wikimedia Commons CC photos of players with
> credit. No betting or bookmaker mentions. No "raund"/"jang" in long videos. Neutral and respectful to every player/club.
> Example done 21 Nov: Messi vs Ronaldo (render template scratch: fut/make.py style — two shirts, scoreboard, category bars).

> **ELEVENLABS CONNECTOR (20 Nov 2026) — WINS over any "use ElevenLabs-ee62b10f only" line in your task prompt:**
> the "ElevenLabs-ee62b10f" connector is often disconnected. If its tools are missing or error, use the other connector
> named **"ElevenLabs"** — it is now signed in to the SAME paid B2BSAS account, so the same voice_ids work
> (269BA7xEbcFPbGfqUFwe, cZs7lwgnHDDa1vRHHGT1, TUQNWEvVPBLzMBSVDPUA, EaGhLW8G52a4yYz9ESds …). Never skip a video because of this.

> **SIMPLE-LANGUAGE RULE (owner, 19 Nov 2026) — ONLY CineMatrix and GLITCHVERSE (NOT Taqqos, Sog'liq, OUJ, B2B):**
> plain everyday language that anyone understands at first listen — like an adult telling a friend, NOT childish
> (no baby talk, no cartoon tone, no "bolajonlar"). Short sentences (≤ 10–12 words), one idea per sentence, common words
> instead of bookish ones, round numbers, an occasional question to the viewer. No slang insults. Facts stay exact and sourced.

> **TELEGRAM DELIVERY (19 Nov 2026) — WINS over EVERY Telegram instruction in your task prompt or in render/prompts/*:**
> the n8n relay (`mia-z7.app.n8n.cloud/.../z7-telegram-send`, n8n execute_workflow) is DEAD — never use it, never use AnythingMCP.
> Send with Supabase MCP `execute_sql` on project `vtsurdinopzycwsfzsuk`, one message per call:
> `select public.z7_tg('<chat_id>','message','<html text>');` — video: `select public.z7_tg('<chat_id>','video',null,'<https mp4 ≤20 MB>','<html caption>');`
> (photo: kind 'photo'). It returns a request id; after ~3 s check `select status_code, content from net._http_response where id = <id>;` → 200 = sent.
> Same allowed chats as before. Fallback only if that fails: GitHub branch tg-outbox (tg/<date>_<task>_<n>.json); else put the text in your final reply.

> **TAQQOS OWNER RULES (16 Nov 2026) — read first if you produce ANY Taqqos video (daily "Kim kuchli?", Bilasizmi, Tarix, long, Xarita):**
> 1. Follow `render/prompts/taqqos_growth.md` — it WINS over older Taqqos instructions in your task prompt
>    (no country repeat within 60 days, new theme/angle every day, surprise hook in frame 1, change ≥2 visual elements,
>    22–30 s Shorts, loop ending, one debate question).
> 2. NO WHOOSH anywhere — not in render jobs, not in locally generated audio (taqqosNN.py / own SFX mixes), not on cuts,
>    rounds or hooks. Only very soft tick/pop allowed. (Owner, 14 Nov.) Booms on hooks also off for Taqqos.
> 3. Taqqos Tarix now runs only on Sunday. New rubric "Xarita" (map redrawn by data) runs Tue + Fri 18:00 Tashkent:
>    brief in `render/prompts/taqqos_xarita.md`. New rubric "Grafik" (self-drawing chart + "nega aynan?") runs Thu 18:00 Tashkent: `render/prompts/taqqos_grafik.md`. Don't schedule another Taqqos Short within 1 h of them.

Free, watermark-free, 1080x1920 30 fps renderer running on GitHub Actions (branch `render`).
The user wants top ("1000") quality on every channel. Use this INSTEAD of vidiq_compose / trim_media / VideoDB.

## How to render
1. `add_repo` z7992266-sketch/AI_Video_Imperiya_New (access push); `git clone --branch render --single-branch <url> rw`.
2. Write `rw/render/jobs/<channel>_<YYYYMMDD>_<slug>.json` (unique name; never reuse a name). Spec = docstring of `render/render.py`.
   Every `src` must be a direct https download: Pexels `https://www.pexels.com/download/video/<ID>/`, Wikimedia
   `upload.wikimedia.org` image, Kling / ElevenLabs result URLs, vidIQ signed URLs, `raw.githubusercontent.com` files
   (commit your own local renders/images to branch `media` first), or an earlier render release URL.
   ElevenLabs content URLs expire after ~2 h: push the job right after generating the voice.
3. `git add` + commit + `git push origin render`. The workflow "Z7 Render" renders it (2-6 min).
4. Wait with a background loop: `git fetch -q origin render` every 30 s (max 25 min) until
   `git show FETCH_HEAD:render/out/<name>.json` exists. `"ok": true` -> `"url"` (mp4) and `"thumb"` (jpg) are public
   release URLs. `"ok": false` -> read `"error"`, fix the job, push it again under a new name.
5. QA before posting: `ffmpeg -ss <t> -i <url> -frames:v 1 f.jpg` for 5-6 moments (hook, mid, captions, end card)
   and look at them with Read: text inside the frame, captions match the voice, no black/broken frames.
   (Direct downloads of github.com release URLs may be blocked in the sandbox; then use
   `gh api repos/z7992266-sketch/AI_Video_Imperiya_New/releases/tags/renders` to get the asset id and
   `gh api -H "Accept: application/octet-stream" repos/.../releases/assets/<id> > v.mp4`.)
6. `vidiq_video_upload(url=<render url>)` is FREE -> uploadId. Put that uploadId in the Drive log exactly where the old
   steps put the "final vidIQ uploadId" (the posting tasks use it), and also log `RENDER URL: <url>`.

## Quality bar
- Frame 1 = the most striking shot + `hook` text (2-5 words); movement from the first frame.
- Scenes 2-3.5 s, vary `move` (in / right / out / left / up) — or leave `"auto"`; `transition: "auto"`.
- `captions.script` = the exact narration text -> word-by-word karaoke captions (yellow active word).
  Use `"style": "none"` when the video already has its own text (e.g. Taqqos motion graphics).
- `grade`: `cinematic` (default), `dark` (mystery/horror/storm), `clean` (bright/product).
- `music`: own track URL, or generated `{"gen": "dark" | "tension" | "calm"}`; ducks under the voice automatically.
- Whoosh is OFF by default (owner 14 Nov 2026: no whoosh at all); boom on the hook only for non-Taqqos channels (`"sfx": false` to disable).
- `endcard`: title/subtitle/small text card (or `image`). `badge` for "Made by B2B SAS" etc.
- Audio is normalised to -14 LUFS (YouTube/Instagram standard).
- Pre-rendered video (e.g. Taqqos local motion render) + separate narration: one scene with
  `"native_audio": true, "move": "none", "grade": "none"`, top-level `"native_audio": true`, `"voice": {...}`,
  `"captions": {"style": "none"}`, `"transition": "none"`, `"sfx": false`.

## New features (30 Oct 2026)
- Scene `fx`: list of `punch`, `shake`, `glitch`, `glitch_end`, `flash`, `grain`. Video scenes: `reverse: true`.
- `voices`: extra voice tracks `[{"src","start","volume","fx": "phone"|"echo"|"whisper"}]`.
- `sfx_events`: `[{"t","type": ring|zap|heartbeat|tick|boom|rewind|whoosh|riser,"volume"}]` (+ `sfx_events_volume`).
- `texts`: timed overlays `[{"t0","t1","text","pos","size","color","pop"}]`.
- `fade_in` (default 0 when a hook exists), `fade_out: 0` for seamless loops; `transition: "none"` = hard cuts.
- Captions: `captions.words` (exact timing) or `captions.segments` `[{"src","start","script"}]` for multi-voice timing.
  Best sync: run silencedetect on each voice and give phrase-level `words` timing.
- Signed URLs (ElevenLabs etc.) expire in ~2 h: copy media into `render/assets/<job>/` and use repo-relative paths.
- RE-RENDER: a job is skipped while `render/out/<name>.json` exists. Delete that json AND change the job file
  (e.g. bump `"rev"`) in the same push, otherwise the workflow does not run.
- Grain makes files big (~110 MB/45 s at crf 18). That is fine for YouTube/Metricool (public release URL works as media).

## Template "bilasizmi" — BILASIZMI? cloud-fact Shorts (Taqqos, 10 Nov 2026)
Owner brief: each fact photo sits INSIDE a cartoon cloud, strong animation everywhere. Renderer: `render/bilasizmi.py`
(numpy/PIL/cv2 frames -> ffmpeg; reuses `render.py` fetch / compress_pauses / gen_events (SFX 40 %); two-pass loudnorm -14 LUFS).
- Job = `render/jobs/<name>.json` with `"template": "bilasizmi"` -> render.yml routes it to `render/bilasizmi.py`
  (any job with `"template": "<x>"` runs `render/<x>.py` if it exists). Output, release upload and `render/out/<name>.json`
  are the same as for normal jobs. Full spec in the docstring of `render/bilasizmi.py`; example:
  `render/jobs/taqqos_bil_20261110_landlocked.json`.
- Fields: `title` ("BILASIZMI?"), `brand` ("TAQQOS"), `voice` {src, start, max_pause, fit}, `words` (ElevenLabs
  `creative_transcribe_audio` word list as `{"w","t0","t1"}`, voice-file seconds), `facts[]` {image, credit, at / at_word,
  focus, zoom, number (dict or list: value, from, prefix, suffix, label, at_word, dur)}, `endcard` {at_word, dur, title, line,
  button}, `music` {"gen": "bright"} (generated, copyright-free), `sfx`.
- Script: 70–85 words, hook "Bilasizmi? …" -> 2–3 facts -> question; numbers written as words; one ElevenLabs take
  (voice 269BA7xEbcFPbGfqUFwe, eleven_v3, generations_count 1). eleven_v3 reads ~2.1 words/s, so use
  `"max_pause": 0.16, "fit": 33` to land at 30–35 s (tempo is capped at 1.12).
- Images: Wikimedia Commons PD/CC0/CC BY/CC BY-SA or NASA only; put author + licence in `credit` and in the description.
  Copy voice + images into `render/assets/<job>/` (signed URLs expire) and use repo-relative paths.
- Layout is fixed to the Shorts safe area (text between 12 % and 82 % of the height): header y≈284, cloud centre y 862,
  counter y 1290, captions y 1452, credit y 1540. Earth-from-space style square photos: `"zoom": [1.08, 1.18]`.
- Local preview of single frames: `BIL_PREVIEW=0.5,5,12 RENDER_WORK=/tmp/w python3 render/bilasizmi.py job.json /dev/null`
  writes `/tmp/w/prev_*.jpg` (no encode) — check them before pushing.
