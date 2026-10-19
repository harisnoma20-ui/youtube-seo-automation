"""
Video Upload Automation — Google Drive se YouTube tak
-------------------------------------------------------------------
Kaam: Google Drive ke ek folder ("ToUpload") mein aapki ready videos
(voice ke sath) daali jati hain. Ye module unhe dhoondh kar, AI se SEO
generate karke, YouTube pe upload kar deta hai, aur file ko "Uploaded"
folder mein move kar deta hai (taake dobara process na ho).

Zaroori: OAuth credentials mein "drive" scope already add hai
(seo_automation.py ke get_oauth_credentials() mein).
"""

import os
import io
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
DOWNLOAD_DIR = "downloaded_videos"
CHANNEL_SHORT_MAX_SECONDS = 40
SHORT_DURATION_TOLERANCE_SECONDS = 0.5
CHANNEL_LONG_MIN_SECONDS = 60


def probe_video(file_path):
    """Return duration and dimensions using ffprobe (available on GitHub runners)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", file_path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    if not streams:
        raise ValueError("Video stream nahi mili.")
    stream = streams[0]
    return {
        "duration_seconds": float(payload.get("format", {}).get("duration", 0)),
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
    }


def validate_short_eligibility(file_path):
    """Accept only this channel's vertical/square Shorts of up to 40 seconds."""
    info = probe_video(file_path)
    if (
        info["duration_seconds"]
        > CHANNEL_SHORT_MAX_SECONDS + SHORT_DURATION_TOLERANCE_SECONDS
    ):
        raise ValueError(
            "Shorts folder ki video %.2f seconds hai. Is channel ka Shorts rule "
            "maximum 40 seconds hai. Isay 40-second ya chhote vertical clip mein "
            "export karein."
            % info["duration_seconds"]
        )
    if info["width"] > info["height"]:
        raise ValueError(
            "Shorts folder ki video landscape (%sx%s) hai. YouTube Short ke liye "
            "square ya vertical export required hai."
            % (info["width"], info["height"])
        )
    return info


def validate_long_eligibility(file_path):
    """Accept only videos longer than 60 seconds in the long-video folder."""
    info = probe_video(file_path)
    if info["duration_seconds"] <= CHANNEL_LONG_MIN_SECONDS:
        raise ValueError(
            "Long Videos folder ki video %.1f seconds hai. Long video ke liye "
            "duration 60 seconds se zyada honi chahiye. 41-60 second videos "
            "upload nahi ki jayengi."
            % info["duration_seconds"]
        )
    return info


def list_new_drive_videos(drive_service, folder_id):
    """'ToUpload' Drive folder mein jitni bhi video files hain, unki list lana."""
    query = f"'{folder_id}' in parents and trashed = false"
    response = drive_service.files().list(
        q=query, fields="files(id, name, mimeType)"
    ).execute()
    videos = [
        f for f in response.get("files", [])
        if f.get("mimeType", "").startswith("video/")
    ]
    return sorted(videos, key=lambda item: natural_filename_key(item["name"]))


def natural_filename_key(file_name):
    """Sort numbered names naturally: 1, 2, 3, 10 instead of 1, 10, 2."""
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", file_name)
    ]


def topic_from_filename(file_name):
    """Remove queue number and repeated video extensions before SEO generation."""
    topic = re.sub(r"(?:\.(?:mp4|mov|m4v|webm|avi))+$", "", file_name, flags=re.I)
    topic = re.sub(r"^\s*\d+\s*[-_. )]+\s*", "", topic)
    return topic.strip() or file_name


def download_drive_file(drive_service, file_id, file_name):
    """Drive se video ko GitHub Actions ke temporary storage mein download karna."""
    from googleapiclient.http import MediaIoBaseDownload

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    destination_path = os.path.join(DOWNLOAD_DIR, file_name)
    request = drive_service.files().get_media(fileId=file_id)
    with io.FileIO(destination_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return destination_path


def upload_video_to_youtube(
    youtube,
    file_path,
    title,
    description,
    tags,
    privacy_status="public",
    publish_at=None,
    category_id="27",
    video_language="en",
    made_for_kids=False,
    contains_synthetic_media=True,
):
    """Video ko YouTube pe upload karna. Agar publish_at diya jaye (ISO format,
    e.g. '2026-08-30T21:00:00Z'), to video 'private' upload hogi aur khud-ba-khud
    usi waqt PUBLIC ho jayegi — matlab upload turant ho sakta hai, lekin
    audience ke peak time pe hi public hogi."""
    from googleapiclient.http import MediaFileUpload

    status = {"privacyStatus": "private", "publishAt": publish_at} if publish_at else {"privacyStatus": privacy_status}
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags[:15],
            "categoryId": str(category_id),
            "defaultLanguage": video_language,
            "defaultAudioLanguage": video_language,
        },
        "status": {
            **status,
            "selfDeclaredMadeForKids": made_for_kids,
            "containsSyntheticMedia": contains_synthetic_media,
        },
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]


def move_drive_file(drive_service, file_id, from_folder_id, to_folder_id):
    """Upload hone ke baad file ko 'Uploaded' folder mein move karna, taake dobara upload na ho."""
    drive_service.files().update(
        fileId=file_id,
        addParents=to_folder_id,
        removeParents=from_folder_id,
        fields="id, parents",
    ).execute()


def calculate_next_publish_time(target_hour_utc, allowed_weekdays=None, now=None):
    """Return the next future publishing slot on an allowed UTC weekday.

    Python weekdays use Monday=0 through Sunday=6. This also makes a manual
    workflow run respect the channel's long/Shorts publishing calendar.
    """
    now = now or datetime.now(timezone.utc)
    allowed = set(range(7) if allowed_weekdays is None else allowed_weekdays)
    if not allowed:
        raise ValueError("Kam az kam aik upload weekday configure karein.")

    for day_offset in range(8):
        candidate_day = now + timedelta(days=day_offset)
        candidate = candidate_day.replace(
            hour=target_hour_utc,
            minute=0,
            second=0,
            microsecond=0,
        )
        if candidate.weekday() in allowed and candidate > now:
            return candidate.strftime("%Y-%m-%dT%H:%M:%SZ")

    raise ValueError("Agla publishing slot calculate nahi ho saka.")


def cleanup_downloaded_file(file_path):
    """GitHub Actions runner se temporary file delete karna (storage bachane ke liye)."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Temp file delete karte waqt error: {e}")
