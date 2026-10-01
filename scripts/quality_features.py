"""
Quality Features Module — Auto-Thumbnail Fix, Caption Improvement, Quota Safety
-------------------------------------------------------------------------------
1. AUTO-THUMBNAIL FIX: Jab diagnosis 'THUMBNAIL' issue baar-baar flag kare, ye
   module khud ek naya thumbnail (title-text overlay ke sath, styled background)
   generate karke YouTube pe set kar deta hai — 'detect + fix' dono khud hote hain.

2. CAPTION IMPROVEMENT: YouTube khud video upload hone ke kuch der baad
   auto-captions (ASR) generate karta hai. Ye module un auto-captions ko
   nikaal kar AI se saaf/behtar (punctuation, clarity) karke wapas ek
   improved caption track ke tor pe upload kar deta hai.
   NOTE: Ye 'text improvement' hai, scratch se generation nahi — kyunke
   humein video ka actual transcript nahi milta, sirf YouTube ke apne ASR
   captions milte hain jo hum behtar karte hain.

3. QUOTA SAFETY: YouTube Data API ki daily limit (10,000 units) hoti hai.
   Ye module andaza rakhta hai ke is run mein kitni units use ho chuki hain,
   aur agar limit ke paas pahunch jayein to non-critical operations
   (competitor tracking, comments) skip kar deta hai taake critical
   operations (SEO update, upload) fail na hon.
"""

import os
import re
import io
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Approximate YouTube Data API v3 unit costs (Google ke official quota docs se)
QUOTA_COSTS = {
    "search": 100,
    "videos_list": 1,
    "videos_update": 50,
    "videos_insert": 1600,
    "comment_insert": 50,
    "thumbnail_set": 50,
    "captions_list": 50,
    "captions_download": 200,
    "captions_insert": 400,
}


# ========== QUOTA SAFETY ==========
class QuotaTracker:
    """Is run mein andazan kitni quota units use hui, uska hisaab rakhna."""

    def __init__(self, safety_limit=9000):
        self.used = 0
        self.safety_limit = safety_limit

    def add(self, operation):
        cost = QUOTA_COSTS.get(operation, 0)
        self.used += cost
        return self.used

    def can_afford(self, operation):
        cost = QUOTA_COSTS.get(operation, 0)
        return (self.used + cost) <= self.safety_limit

    def status_message(self):
        return f"Quota estimate: {self.used}/{self.safety_limit} units is run mein use hui."


# ========== AUTO-THUMBNAIL FIX ==========
def _get_font(size):
    """System font dhoondhna — agar na mile to PIL ka default font use hoga."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_thumbnail(title_text, output_path, bg_color_top=(20, 20, 40), bg_color_bottom=(60, 20, 60)):
    """FALLBACK thumbnail — jab video file available na ho (e.g. purani video
    ka thumbnail escalation-fix karte waqt). Sirf text + gradient hota hai,
    video ke actual scene se koi taluq nahi. Jahan ho sake, generate_thumbnail_from_video()
    use karein — wo asal video ka frame use karta hai."""
    img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), bg_color_top)
    draw = ImageDraw.Draw(img)

    # Vertical gradient background
    for y in range(THUMBNAIL_HEIGHT):
        ratio = y / THUMBNAIL_HEIGHT
        r = int(bg_color_top[0] + (bg_color_bottom[0] - bg_color_top[0]) * ratio)
        g = int(bg_color_top[1] + (bg_color_bottom[1] - bg_color_top[1]) * ratio)
        b = int(bg_color_top[2] + (bg_color_bottom[2] - bg_color_top[2]) * ratio)
        draw.line([(0, y), (THUMBNAIL_WIDTH, y)], fill=(r, g, b))

    _draw_title_text(draw, title_text)
    img.save(output_path, "JPEG", quality=92)
    return output_path


def get_local_video_duration(video_path):
    """ffprobe se local video file ki duration (seconds) nikalna."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, timeout=15, text=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Video duration nikalne mein error: {e}")
        return None


def extract_video_frame(video_path, output_path, timestamp_seconds=None, video_duration_seconds=None):
    """ffmpeg se video ke ek frame ko image ki tarah nikalna — is se asal
    scene/story-relevant thumbnail banti hai, generic background nahi.
    Agar timestamp na diya jaye, video ke ~35% waqt ka frame liya jata hai
    (aksar story mein is point tak koi dramatic/interesting scene aa chuki hoti hai,
    shuru ke plain/intro frames se behtar)."""
    if timestamp_seconds is None:
        timestamp_seconds = (video_duration_seconds * 0.35) if video_duration_seconds else 3

    result = subprocess.run(
        ["ffmpeg", "-y", "-ss", str(timestamp_seconds), "-i", video_path,
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True, timeout=30,
    )
    if result.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError(f"Frame extract nahi ho saka: {result.stderr.decode(errors='ignore')[:300]}")
    return output_path


def generate_thumbnail_from_video(video_path, title_text, output_path, video_duration_seconds=None):
    """ASAL video se ek frame nikaal kar, uske upar title text overlay karna
    (bottom mein dark gradient taake text readable rahe). Ye story/video se
    genuinely related thumbnail banata hai — sirf generic background nahi."""
    if video_duration_seconds is None:
        video_duration_seconds = get_local_video_duration(video_path)

    frame_path = output_path.replace(".jpg", "_frame.jpg")
    extract_video_frame(video_path, frame_path, video_duration_seconds=video_duration_seconds)

    img = Image.open(frame_path).convert("RGB").resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    # Bottom half pe dark gradient overlay — taake text kisi bhi frame pe readable rahe
    overlay = Image.new("RGBA", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for y in range(THUMBNAIL_HEIGHT // 2, THUMBNAIL_HEIGHT):
        alpha = int(180 * ((y - THUMBNAIL_HEIGHT // 2) / (THUMBNAIL_HEIGHT // 2)))
        overlay_draw.line([(0, y), (THUMBNAIL_WIDTH, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    _draw_title_text(draw, title_text, bottom_aligned=True)

    img.save(output_path, "JPEG", quality=92)
    if os.path.exists(frame_path):
        os.remove(frame_path)
    return output_path


def _draw_title_text(draw, title_text, bottom_aligned=False):
    """Title text ko wrap karke, outline ke sath, image pe draw karna (shared
    logic dono thumbnail generation functions ke liye)."""
    font = _get_font(80 if bottom_aligned else 90)
    words = title_text.upper().split()
    lines, current_line = [], ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > THUMBNAIL_WIDTH - 120:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    lines = lines[:3]

    line_height = 100 if bottom_aligned else 110
    total_height = len(lines) * line_height
    start_y = (THUMBNAIL_HEIGHT - 60 - total_height) if bottom_aligned else (THUMBNAIL_HEIGHT - total_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (THUMBNAIL_WIDTH - text_width) // 2
        y = start_y + i * line_height
        for dx, dy in [(-3, -3), (-3, 3), (3, -3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))


def set_video_thumbnail(youtube, video_id, thumbnail_path):
    """Generate ki gayi thumbnail ko YouTube pe upload/set karna."""
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f"Naya thumbnail set ho gaya video {video_id} ke liye.")


# ========== CAPTION IMPROVEMENT ==========
def get_auto_caption_track(youtube, video_id, language="en"):
    """Video pe YouTube ke khud-generate kiye hue (ASR) caption track ko dhoondhna."""
    response = youtube.captions().list(part="snippet", videoId=video_id).execute()
    for item in response.get("items", []):
        snippet = item["snippet"]
        if snippet.get("trackKind") == "ASR" and snippet.get("language", "").startswith(language):
            return item["id"]
    return None


def improve_caption_text(raw_caption_text):
    """AI se raw ASR caption ko saaf/behtar (punctuation, clarity) karna."""
    prompt = f"""Ye YouTube ke auto-generated (ASR) captions hain, jinme punctuation
aur clarity ki kami hoti hai:

{raw_caption_text[:3000]}

Isay clean karo: sahi punctuation, capitalization, aur clarity ke sath. Meaning
ya timing structure mat badalna, sirf text quality behtar karo. Sirf cleaned
text return karo, kuch aur nahi."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def download_caption_track(youtube, caption_id):
    """Caption track ko SRT format mein download karna."""
    request = youtube.captions().download(id=caption_id, tfmt="srt")
    result = request.execute()
    return result.decode("utf-8") if isinstance(result, bytes) else result


def upload_improved_caption(youtube, video_id, srt_text, language="en", name="Improved (AI-cleaned)"):
    """Improved caption ko naye track ke tor pe YouTube pe upload karna."""
    from googleapiclient.http import MediaIoBaseUpload
    media = MediaIoBaseUpload(io.BytesIO(srt_text.encode("utf-8")), mimetype="text/plain", resumable=False)
    youtube.captions().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id, "language": language, "name": name, "isDraft": False}},
        media_body=media,
    ).execute()
    print(f"Improved caption upload ho gaya video {video_id} ke liye.")
