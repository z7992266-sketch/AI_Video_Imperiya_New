# AI_Video_Imperiya_New

Har kuni o'zbek tilida ovozli va subtitrli qisqa vertikal video yaratib, Telegram / YouTube Shorts / Instagram Reels'ga joylaydigan multi-agent loyiha.

## Agentlar
1. **Ssenarist** (`scriptwriter.py`) — OpenRouter'ning faqat bepul (`:free`) modellari; biri ishlamasa keyingisiga o'tadi.
2. **Diktor** (`voice.py`) — Edge TTS, `uz-UZ-MadinaNeural`.
3. **Rassom** (`visual.py`) — pollinations.ai tasvirlari (xato bo'lsa gradient zaxira).
4. **Montajchi** (`editor.py`) — ffmpeg: 1080x1920, subtitr, zoom effekti.
5. **Nashr qiluvchi** (`publisher.py`) — Telegram Bot API, YouTube Data API, Instagram Graph API.

## Tez sozlash (bitta buyruq)
```bash
gh auth login
./setup_github.sh            # public repo (Instagram uchun)  |  ./setup_github.sh --private
```
Skript repo yaratadi, kodni yuklaydi, kalitlarni so'rab GitHub Secrets'ga soladi va birinchi ishga tushirishni boshlaydi.

## GitHub Actions bilan qo'lda sozlash
Repo -> Settings -> Secrets and variables -> Actions -> **New repository secret**:

| Secret | Qayerdan olinadi |
|---|---|
| `OPENROUTER_API_KEY` | openrouter.ai -> Keys (Base URL kodda: `https://openrouter.ai/api/v1`) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | @BotFather; botni kanal/chatga qo'shing |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | Google Cloud Console (YouTube Data API v3, OAuth) |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | Meta for Developers (Instagram Business/Creator akkaunt) |

Kalitsiz platformalar avtomatik o'tkazib yuboriladi. Workflow har kuni 04:00 UTC da ishlaydi; qo'lda ham ishga tushirish mumkin (Actions -> Kunlik video -> Run workflow).

**Eslatma:** Instagram videoni ochiq URL'dan oladi, shuning uchun repo *public* bo'lishi kerak (workflow videoni Release sifatida joylaydi).

## Lokal ishga tushirish
```bash
pip install -r requirements.txt     # ffmpeg va DejaVu shrifti tizimda bo'lishi kerak
cp .env.example .env                # kalitlarni .env ga yozing (GitHub'ga yuklamang!)
python main.py generate             # output/final.mp4
python main.py publish
```
Mavzular `topics.txt` da (kun bo'yicha aylanadi), yoki `--topic "..."`.

## Cheklovlar
- Bepul OpenRouter modellarida kunlik/daqiqalik limit bor ("cheksiz" emas); modellar vaqt o'tishi bilan o'zgaradi.
- pollinations.ai statik tasvir beradi; video harakati zoom effekti orqali yaratiladi.
