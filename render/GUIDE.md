# Z7 Render — guide for the daily channel tasks

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
- Whoosh on cuts + boom on the hook are added automatically (`"sfx": false` to disable).
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
