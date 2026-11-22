#!/usr/bin/env bash
# Adds the animated New Year tree (render/assets/newyear/archa_overlay.mov, our own drawing, transparent, 4 s loop)
# to a finished video. Usage: newyear_overlay.sh in.mp4 out.mp4 [top-right|top-left|bottom-left] [width_px]
# Vertical 1080x1920 default: top-right, 170 px wide, below the YouTube/Instagram top UI (y=280).
# 16:9 default: top-right, 150 px wide, 30 px margin. Audio is copied unchanged.
set -e
IN="$1"; OUT="$2"; CORNER="${3:-top-right}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
OV="$DIR/assets/newyear/archa_overlay.mov"
read VW VH < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$IN" | tr ',' ' ')
if [ "$VH" -gt "$VW" ]; then TW="${4:-170}"; MX=36; TOP=280; BOT=$((VH*20/100)); else TW="${4:-150}"; MX=30; TOP=30; BOT=40; fi
case "$CORNER" in
  top-left)    POS="x=$MX:y=$TOP" ;;
  bottom-left) POS="x=$MX:y=H-h-$BOT" ;;
  *)           POS="x=W-w-$MX:y=$TOP" ;;
esac
ffmpeg -y -loglevel error -i "$IN" -stream_loop -1 -i "$OV" \
  -filter_complex "[1:v]scale=$TW:-1,format=rgba[t];[0:v][t]overlay=$POS:shortest=1:format=auto,format=yuv420p[v]" \
  -map "[v]" -map 0:a? -c:v libx264 -crf 18 -preset medium -c:a copy -movflags +faststart "$OUT"
echo "newyear overlay OK -> $OUT ($CORNER, ${TW}px)"
