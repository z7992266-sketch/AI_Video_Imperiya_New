# Taqqos renderer (used by the daily scheduled task)
- `taqqos2.py` — template (episode 2: UZ vs KZ). Copy to `taqqosNN.py`, edit B country name/flag (`flag_tr`), colours, ROUNDS (6 verified metrics, `win` = "uz"/"tr"), and the outro texts (win / tie).
- Timing: `TIMING_JSON` = {"intro": first round start-0.12, "rounds": [...], "outro": ...} from ElevenLabs word timestamps; `WORDS_JSON` = {"words":[{text,start,end}...]} for kinetic captions.
- Sound bed: `audio2.py` (import line points at the episode module) -> audio.wav
- Render: `python3 taqqosNN.py | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i audio.wav -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -shortest out.mp4`
- Host: commit the mp4 to this `media` branch; raw.githubusercontent URL is reachable by VideoDB/vidIQ/Telegram.
- Final mix (narration on top): VideoDB upload_media (video + narration audio) -> render_timeline (video volume 0.45, narration 1.3) -> download_timeline_render -> vidiq_video_upload (free) -> Telegram.
