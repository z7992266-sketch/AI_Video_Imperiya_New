Telegram outbox: add one NEW JSON file per message (e.g. tg/2026-11-01_ouj_1.json), commit, push to branch tg-outbox.
Fields: chat_id (8355820653, -1004456004836, -1004357664340, -1004379758095, -1004281112365), kind (message|video|photo), text (HTML), file_url + caption (video/photo, public https, video <= 20 MB).
