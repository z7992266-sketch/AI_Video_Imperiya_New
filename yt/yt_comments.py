"""Taqqos YouTube comments via the official YouTube Data API v3 (free, no vidIQ).
fetch: unanswered top-level comments -> yt/inbox/taqqos.json
post : yt/replies/pending.json [{"parentId": "...", "text": "..."}] -> posted, log in yt/replies/done/
Secrets (owner adds them himself in GitHub -> Settings -> Secrets -> Actions): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import json, os, sys, time, urllib.request, urllib.parse
CH = os.environ.get("YT_CHANNEL", "UCjxj5-qg5FV5GOb5Li5PiaA")  # Taqqos_Uz
API = "https://www.googleapis.com/youtube/v3/"

def token():
    data = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                   "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))["access_token"]

def call(tok, path, params=None, body=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
                                 method="POST" if body else "GET")
    return json.load(urllib.request.urlopen(req))

def fetch(tok):
    out, page = [], None
    for _ in range(4):  # newest 200 threads, 1 quota unit per page
        p = {"part": "snippet,replies", "allThreadsRelatedToChannelId": CH, "maxResults": 50, "order": "time", "textFormat": "plainText"}
        if page: p["pageToken"] = page
        r = call(tok, "commentThreads", p)
        for t in r.get("items", []):
            top = t["snippet"]["topLevelComment"]; s = top["snippet"]
            if s.get("authorChannelId", {}).get("value") == CH: continue
            if any(c["snippet"].get("authorChannelId", {}).get("value") == CH for c in t.get("replies", {}).get("comments", [])): continue
            out.append({"parentId": top["id"], "videoId": t["snippet"].get("videoId"), "author": s.get("authorDisplayName"),
                        "text": s.get("textDisplay"), "published": s.get("publishedAt"), "likes": s.get("likeCount", 0),
                        "replies": t["snippet"].get("totalReplyCount", 0)})
        page = r.get("nextPageToken")
        if not page: break
    os.makedirs("yt/inbox", exist_ok=True)
    json.dump({"fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "channel": CH, "unanswered": out},
              open("yt/inbox/taqqos.json", "w"), ensure_ascii=False, indent=1)
    print("unanswered:", len(out))

def post(tok):
    f = "yt/replies/pending.json"
    if not os.path.exists(f): print("no pending"); return
    items = json.load(open(f)); done = []
    for it in items[:40]:  # 50 units each; daily quota 10,000
        t = (it.get("text") or "").strip()
        if not t or "<" in t or ">" in t: done.append({**it, "status": "skipped"}); continue
        try:
            r = call(tok, "comments", {"part": "snippet"}, {"snippet": {"parentId": it["parentId"], "textOriginal": t[:1000]}})
            done.append({**it, "status": "posted", "replyId": r.get("id")})
        except Exception as e:
            done.append({**it, "status": "error", "error": str(e)[:300]})
        time.sleep(2)
    os.makedirs("yt/replies/done", exist_ok=True)
    json.dump(done, open("yt/replies/done/%s.json" % time.strftime("%Y%m%d_%H%M%S"), "w"), ensure_ascii=False, indent=1)
    os.remove(f)
    print({s: sum(1 for d in done if d["status"] == s) for s in ("posted", "skipped", "error")})

if __name__ == "__main__":
    for mode in sys.argv[1:]:
        globals()[mode](token())
