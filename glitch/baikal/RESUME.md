# Mia's Glitch Diary #14 — Lake Baikal ice rings (long, 16:9) — PREPARED, NOT VOICED

Status 25 Nov 2026: script, sources, visuals, credits, renderer ready. BLOCKED on ElevenLabs credits:
account had 2,024 credits left (119,184 / 121,208 used; reset 30 Nov 2026 22:05 UTC); narration needs ~5,600.

## Resume (after credits are available)
1. Workdir /home/claude/gv: copy this folder there; copy fetch-media:fetch/out/gv14_*.jpg into /home/claude/gv/assets/;
   copy glitch/tunguska/../logo_800.png (glitch/logo_800.png) to /home/claude/gv/.
2. Voice: ElevenLabs voice PsKMqMIop7GPtO4mtwQj, eleven_multilingual_v2, generations_count 1, chunk1.txt (2,395) /
   chunk2.txt (1,951) / chunk3.txt (1,249) chars ≈ 5,600 credits. Download via fetch-media as gv14_vo1..3.mp3 -> assets/.
3. python3 timing.py  (writes real timing.json; current timing.json is a 15 chars/s placeholder)
4. python3 build.py --still <t,...> for QA; python3 build.py --part 0 2 & --part 1 2 ; concat; python3 audio.py (needs kit/render) ; mux.
5. Description: description_draft.txt (fill chapter timestamps + credits list from credits.json).
Release slot used by the routine: Saturday 17:00 Europe/Moscow, Metricool blog 7653042, YouTube "video".
