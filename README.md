# Z7 Render (branch `render`)
Professional 1080x1920 renderer (ffmpeg, no watermark). Push `render/jobs/<name>.json` -> GitHub Actions renders it
and publishes `<name>.mp4` + `<name>.jpg` to the `renders` release; result info in `render/out/<name>.json`.
Spec: see the docstring in `render/render.py`.
