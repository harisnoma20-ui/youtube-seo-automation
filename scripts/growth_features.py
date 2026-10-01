"""
Growth Features Module — Advanced additions to YouTube Auto-SEO System
-------------------------------------------------------------------------
Ye 6 features add karta hai:
  1. Weekly Summary Report -> poore channel ka growth trend, best/worst video
  2. Trending Surge Alert -> agar koi keyword achanak spike kare, turant alert
  3. Keyword Learning Loop -> jo keywords views la rahe hain, unhe future mein prioritize karna
  4. Community Post Ideas -> AI se draft ideas (auto-post nahi ho sakta, API support nahi karti)
  5. Auto Pinned Comment -> comment auto-post hota hai (pin karna manual hai, API isay support nahi karti)
  6. Competitor Tracking -> niche ke top videos/channels dekh kar unke title-patterns nikalna

IMPORTANT HONESTY NOTE:
  YouTube Data API 'pin comment' ko officially support nahi karti — is liye
  comment auto-post ho jata hai, lekin pin karna aapko YouTube Studio mein
  khud ek click se karna hoga. Isi tarah, Community tab post bhi API se
  create nahi ho sakta — system sirf ideas generate karke WhatsApp pe
  bhejega, post karna manual hoga.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from pytrends.request import TrendReq
from openpyxl import load_workbook

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TRACKING_FILE = "tracking_sheet.xlsx"
WINNING_KEYWORDS_FILE = "winning_keywords.json"
SURGE_THRESHOLD_MULTIPLIER = 1.8  # Current interest, baseline se kitna guna zyada ho to "surge" maana jaye


def _call_groq(prompt, temperature=0.7):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": temperature},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# ========== 1. WEEKLY SUMMARY REPORT ==========
def generate_weekly_summary(tracking_file=TRACKING_FILE):
    """Tracking sheet se poore channel ka growth trend nikalna: best/worst video, total views delta."""
    if not os.path.exists(tracking_file):
        return "Weekly summary: abhi tracking data available nahi hai."

    wb = load_workbook(tracking_file)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    if not rows:
        return "Weekly summary: abhi koi data nahi hai."

    # Har video ki sabse latest row nikalna
    latest_by_video = {}
    for row in rows:
        video_id = row[1]
        latest_by_video[video_id] = row  # Aakhri wali automatically latest rahegi (append order)

    summary_lines = [f"Weekly Summary ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"]
    summary_lines.append(f"Total videos tracked: {len(latest_by_video)}")

    scored = []
    for video_id, row in latest_by_video.items():
        views = row[4] if isinstance(row[4], (int, float)) else 0
        ctr = row[8] if isinstance(row[8], (int, float)) else 0
        scored.append((video_id, views, ctr))

    if scored:
        best = max(scored, key=lambda x: x[1])
        worst = min(scored, key=lambda x: x[1])
        summary_lines.append(f"Best performing: {best[0]} ({best[1]} views, {best[2]}% CTR)")
        summary_lines.append(f"Needs attention: {worst[0]} ({worst[1]} views, {worst[2]}% CTR)")
        total_views = sum(s[1] for s in scored)
        avg_ctr = sum(s[2] for s in scored) / len(scored)
        summary_lines.append(f"Total views (tracked videos): {total_views}")
        summary_lines.append(f"Average CTR: {avg_ctr:.2f}%")

    return "\n".join(summary_lines)


# ========== 2. TRENDING SURGE ALERT ==========
def check_trending_surge(seed_keywords, target_geos=("US", "GB")):
    """Google Trends interest_over_time dekh kar batana ke koi keyword achanak spike to nahi kar raha."""
    surges = []
    seeds = [k.strip() for k in seed_keywords.split(",")][:5]

    for geo in target_geos:
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload(seeds, timeframe='now 7-d', geo=geo)
            df = pytrends.interest_over_time()
            if df.empty:
                continue
            for kw in seeds:
                if kw not in df.columns:
                    continue
                series = df[kw]
                if len(series) < 4:
                    continue
                recent = series.iloc[-1]
                baseline = series.iloc[:-1].mean()
                if baseline > 0 and recent >= baseline * SURGE_THRESHOLD_MULTIPLIER:
                    surges.append(f"SURGE ALERT ({geo}): '{kw}' interest {baseline:.0f} se {recent:.0f} tak badh gaya hai.")
        except Exception as e:
            print(f"Surge check ({geo}) fail hui: {e}")

    return surges


# ========== 3. KEYWORD LEARNING LOOP ==========
def update_keyword_learning(video_id, tags, ctr, winning_file=WINNING_KEYWORDS_FILE):
    """Agar is video ki CTR achi hai, uske tags ko 'winning keywords' list mein add/boost karna."""
    winning = {}
    if os.path.exists(winning_file):
        try:
            with open(winning_file, "r") as f:
                winning = json.load(f)
        except Exception:
            winning = {}

    GOOD_CTR_THRESHOLD = 4.0
    if isinstance(ctr, (int, float)) and ctr >= GOOD_CTR_THRESHOLD:
        for tag in tags:
            winning[tag] = winning.get(tag, 0) + 1

    with open(winning_file, "w") as f:
        json.dump(winning, f, indent=2)


def get_winning_keywords(top_n=5, winning_file=WINNING_KEYWORDS_FILE):
    """Sabse zyada 'score' wale keywords nikalna, taake naye videos ke liye prioritize kiya ja sake."""
    if not os.path.exists(winning_file):
        return []
    try:
        with open(winning_file, "r") as f:
            winning = json.load(f)
        sorted_keywords = sorted(winning.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:top_n]]
    except Exception:
        return []


# ========== 4. COMMUNITY POST IDEAS ==========
def generate_community_post_ideas(niche, trending_keywords):
    """AI se community-tab post ideas generate karna. NOTE: Auto-post nahi hoga,
    kyunke YouTube API Community posts create karna support nahi karti — ye
    sirf WhatsApp pe ideas bhejega, post karna manual hoga."""
    prompt = f"""Niche: {niche}
Trending keywords: {', '.join(trending_keywords[:5])}
YouTube Community tab ke liye 2 chhote, engaging post ideas do (poll, question,
ya teaser type). Sirf JSON return karo: {{"ideas": ["...", "..."]}}"""

    try:
        raw = _call_groq(prompt)
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean).get("ideas", [])
    except Exception as e:
        print(f"Community post ideas generate karte waqt error: {e}")
        return []


# ========== 5. AUTO PINNED COMMENT ==========
def generate_and_post_comment(youtube, video_id, niche):
    """Engaging comment generate karke video pe post karna (channel owner ki taraf se).
    NOTE: YouTube API se comment PIN karna officially support nahi hota — comment
    post ho jayega, lekin pin karne ke liye YouTube Studio mein khud ek click karna hoga."""
    prompt = f"""Niche: {niche}
Ek chhota, engaging comment likho (1-2 lines) jo video ke creator ki taraf se
ho, viewers ko engage karne ke liye (e.g. sawal poochna ya discussion start
karna). Sirf comment text return karo, kuch aur nahi."""

    try:
        comment_text = _call_groq(prompt, temperature=0.9).strip().strip('"')
        youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {"snippet": {"textOriginal": comment_text}},
                }
            },
        ).execute()
        print(f"Comment post ho gaya video {video_id} pe: {comment_text}")
        return comment_text
    except Exception as e:
        print(f"Comment post karte waqt error: {e}")
        return None


# ========== 6. COMPETITOR TRACKING ==========
def track_competitor_titles(youtube_read, niche_keywords, max_results=10):
    """Niche ke top-ranking recent videos (kisi bhi channel ki) dekh kar unke
    titles ka pattern nikalna — taake pata chale abhi kis type ke titles kaam kar rahe hain."""
    try:
        seed = niche_keywords.split(",")[0].strip()
        response = youtube_read.search().list(
            q=seed, part="snippet", type="video", order="viewCount",
            maxResults=max_results,
            publishedAfter=(datetime.now(timezone.utc) - timedelta(days=14)).isoformat().replace("+00:00", "Z"),
        ).execute()
        titles = [item["snippet"]["title"] for item in response.get("items", [])]
        return titles
    except Exception as e:
        print(f"Competitor tracking fail hui: {e}")
        return []
