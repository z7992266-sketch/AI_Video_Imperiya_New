#!/usr/bin/env bash
# Bir martalik sozlash: GitHub repo yaratadi, kodni yuklaydi, kalitlarni Secrets'ga soladi.
# Talab: git va GitHub CLI (gh). Avval:  gh auth login
# Kalitlar skriptga so'raladi va faqat GitHub Secrets'ga yuboriladi; hech qaysi faylga yozilmaydi.
set -euo pipefail

REPO="AI_Video_Imperiya_New"
VISIBILITY="${1:---public}"   # Instagram uchun --public kerak; faqat Telegram/YouTube bo'lsa: ./setup_github.sh --private

gh auth status >/dev/null 2>&1 || { echo "Avval: gh auth login"; exit 1; }

[ -d .git ] || git init -b main
git add -A
git commit -m "Initial commit: AI video multi-agent" || true
gh repo create "$REPO" "$VISIBILITY" --source=. --remote=origin --push

NAME="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Repo: $NAME"

set_secret() {
  local key="$1" label="$2"
  read -r -s -p "$label (bo'sh qoldirsangiz o'tkazib yuboriladi): " value; echo
  [ -n "$value" ] && printf '%s' "$value" | gh secret set "$key" --repo "$NAME" && echo "  -> $key saqlandi"
  return 0
}

set_secret OPENROUTER_API_KEY "OpenRouter API kaliti"
set_secret TELEGRAM_BOT_TOKEN "Telegram bot tokeni"
set_secret TELEGRAM_CHAT_ID   "Telegram chat/kanal ID"
set_secret YT_CLIENT_ID       "YouTube client id"
set_secret YT_CLIENT_SECRET   "YouTube client secret"
set_secret YT_REFRESH_TOKEN   "YouTube refresh token"
set_secret IG_USER_ID         "Instagram user id"
set_secret IG_ACCESS_TOKEN    "Instagram access token"

gh workflow run daily.yml --repo "$NAME" && echo "Birinchi ishga tushirish boshlandi: gh run watch --repo $NAME"
