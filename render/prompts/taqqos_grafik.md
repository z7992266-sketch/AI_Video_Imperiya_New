> Also obey the "5-SINF QOIDASI" (simple friendly language) at the top of render/GUIDE.md.

# TAQQOS "GRAFIK" SHORT — production brief (owner approved 17 Nov 2026)

Owner (17 Nov 2026): "kanal ochmaymiz, Taqqosga olamiz" — take the animated-chart + mystery-question format into Taqqos.
Format: a line/bar chart DRAWS ITSELF on screen over time, then one point suddenly jumps or drops →
"Nega aynan <yil>da?" → the real reason, with source. NO religion, NO numerology, NO politics opinions.
Never copy other creators' videos, designs, titles or music (e.g. @ilmiyot_uz) — our own Taqqos style.
Owner reads short Uzbek (Latin). Decide yourself, ask nothing. Times for the owner in Tashkent time.
Also obey render/prompts/taqqos_growth.md (no repeats, hook, variety, loop, NO WHOOSH).

## 0. Guard
- Today = Asia/Tashkent date. Metricool getScheduledPosts brand 7705124 for the publish day: if a post whose title
  contains "Grafik" or "grafik" is already scheduled/published that day → stop.
- Publish 18:00 Asia/Tashkent (16:00 Europe/Moscow) on the publish day; never within 1 h of another Taqqos post.

## 1. Topic (never repeat — Drive Google Doc "Taqqos Grafik log", create if missing)
Queue (each needs official data + 2 sources for the "why"):
1. O'zbekiston aholisi 1950–2026 (UN WPP / stat.uz) — the curve and the turning points.
2. Dollar kursi (so'm) 1994–2026 (CBU) — "Nega aynan 2017-yil sentyabrda?" (currency liberalisation).
3. Dunyo aholisi 1800–2026 — "Nega 1950dan keyin raketa kabi?"
4. Oltin narxi 1971–2026 (LBMA / World Bank) — biggest jumps and why.
5. Benzin/neft narxi 1970–2026 (Brent, EIA) — 1973, 2008, 2020.
6. Yaponiya aholisi — "nega kamaymoqda?"; 7. Xitoy tug'ilish soni; 8. Internet foydalanuvchilari O'zbekistonda (ITU).
Prefer topics where Uzbek viewers feel personally involved (prices, money, population).

## 2. Visual (our style: Taqqos dark navy, our accent colours, fonts in render/fonts)
Python (matplotlib or Pillow + numpy) frames, 1080x1920, 30 fps, 22–30 s:
- Frame 1: huge question title (2–5 words) + the axis already moving. Hook within 1 s.
- Line draws left→right in sync with narration; year counter ticks; value label follows the pen.
- At the jump: slow-down, glow ring on the point, big number pop ("×3", "+250 %"), then a short card with the reason.
- Source line visible on screen (small, top under title). Text never in the bottom 18 %.
- Loop: last frame returns to the first frame's composition.

## 3. Voice & sound
Uzbek (Latin) 55–80 words, numbers as words, ends with a debate question
("Sizningcha, keyingi sakrash qachon bo'ladi? Izohda yozing!"). ElevenLabs "ElevenLabs-ee62b10f",
voice_id 269BA7xEbcFPbGfqUFwe, eleven_v3, generations_count 1; creative_transcribe_audio for timings; fetch audio
via fetch-media branch. Music render.py gen "tension"/"calm" low; only soft tick/pop SFX. NO WHOOSH, no boom.

## 4. Render, QA, post, report
Same as render/prompts/taqqos_xarita.md steps 5–8 (silent mp4 on fetch-media → render job
render/jobs/taqqos_grafik_<YYYYMMDD>_<slug>.json → QA 6 frames: numbers = narration = sources, readable, loop →
Metricool 7705124 YouTube Short, category EDUCATION, isAiGeneratedContent true, title e.g.
"Dollar kursi grafigi: nega aynan 2017? 📈 #shorts #grafik #taqqos", description with "Manbalar:" and AI-voice line →
Drive "Taqqos Grafik log" → one Uzbek line to 8355820653 "📈 Taqqos Grafik: <mavzu> — <kun> 18:00").
