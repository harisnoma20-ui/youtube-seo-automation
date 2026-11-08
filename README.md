# YouTube Auto-SEO System (Multi-Channel)

GitHub Actions se khud-ba-khud chalta hai (har din 15:00 UTC pe), aur
`channels_config.json` mein jitne channels defined hon, sab ke liye run
karta hai.

## Files
- `channels_config.json` — har channel ka niche, geos, upload days, waghera
- `.github/workflows/seo-automation.yml` — scheduler + secrets wiring
- `scripts/seo_automation.py` — main script (multi-channel loop)
- `scripts/growth_features.py` — weekly summary, surge alert, keyword learning, community ideas, pinned comment, competitor tracking
- `scripts/upload_features.py` — Drive se YouTube upload
- `scripts/quality_features.py` — caption improvement, quota safety, thumbnail helpers
- `scripts/get_refresh_token.py` — apne PC pe ek dafa chalane wali OAuth script
- `scripts/requirements.txt` — Python dependencies

## Channels & Secret Prefixes

Repo multiple channels support karta hai via `channels_config.json` aur GitHub Secrets:

1. **Medieval Channel (`medieval_lives_explained`)**
   - Prefix: `MEDIEVAL_`
   - Upload Days: Shorts (1,3,5 - Tue, Thu, Sat), Long (0 - Mon)
2. **Born to Wild (`born_to_wild`)**
   - Prefix: `WILDLIFE_`
   - Handle: `@borntowild-u9b`
   - Upload Days: Shorts (1,3,5 - Tue, Thu, Sat), Long (6 - Sun)
   - Initial state: `"enabled": false` (Preflight verify hone tak safe disabled)

### Har Channel ke 9 Required Secrets:
- `{PREFIX}YOUTUBE_API_KEY`
- `{PREFIX}YOUTUBE_CHANNEL_ID`
- `{PREFIX}YOUTUBE_OAUTH_CLIENT_ID`
- `{PREFIX}YOUTUBE_OAUTH_CLIENT_SECRET`
- `{PREFIX}YOUTUBE_OAUTH_REFRESH_TOKEN`
- `{PREFIX}DRIVE_SHORTS_TOUPLOAD_FOLDER_ID`
- `{PREFIX}DRIVE_SHORTS_UPLOADED_FOLDER_ID`
- `{PREFIX}DRIVE_LONG_TOUPLOAD_FOLDER_ID`
- `{PREFIX}DRIVE_LONG_UPLOADED_FOLDER_ID`

Optional (agar Drive kisi aur Google account par ho):
- `{PREFIX}DRIVE_OAUTH_CLIENT_ID`
- `{PREFIX}DRIVE_OAUTH_CLIENT_SECRET`
- `{PREFIX}DRIVE_OAUTH_REFRESH_TOKEN`

Shared Secret:
- `GROQ_API_KEY` (AI SEO generation ke liye zaroori)

## Preflight Verification (Read-Only)

GitHub Actions workflow dispatch se `run_mode: preflight` aur specific channel (ya `all`) select karke verify karein:
- Ye step 9 secrets existence check karta hai
- OAuth channel identity aur handle match verify karta hai
- Chaaro Drive folders ki accessibility aur permissions confirm karta hai
- Queue mein kitni videos hain count karta hai (bina download ya upload kiye)

## Shorts folder rule

`DRIVE_SHORTS_TOUPLOAD_FOLDER_ID` ka folder upload intent batata hai, lekin
YouTube classification force nahi karta. Automation upload se pehle file ko
check karti hai: channel rule ke mutabiq duration 50 seconds ya kam (0.5-second
encoder tolerance ke sath) aur aspect ratio square/vertical
hona zaroori hai. Invalid file upload nahi hoti aur `Uploaded` folder mein move
nahi hoti. 10-minute video ko Short banane ke liye pehle usay 50-second ya chhote
vertical clips mein export karna hoga.

## Content-grounded SEO (recommended)

Har video ke saath same base-name wali `.txt` ya `.md` script/brief ToUpload
folder mein rakhein. Misal:

- `01 - What Did Medieval Peasants Eat.mp4`
- `01 - What Did Medieval Peasants Eat.txt`

Automation matching brief ko title, description aur tags banane ke liye ground
truth ke taur par use karegi, aur successful upload ke baad dono files Uploaded
folder mein move kar degi. Brief na ho to filename use hoga, lekin AI ko facts
ya scenes invent karne ki ijazat nahi di jati.

## Premium-country targeting

`target_audience_geos` Google Trends research aur English metadata context ke
liye use hota hai. Organic YouTube recommendations ko country list se force
nahi kiya ja sakta. Medieval channel US, GB, CA aur AU research context, English
metadata, Education category aur 21:00 UTC publishing slot use karta hai.

## Safe defaults

`enable_metadata_refresh` aur `enable_auto_comment` filhaal `false` hain.
Nayi upload ko SEO metadata milti rahegi, lekin purani published videos ke
titles/descriptions/tags automatically rewrite nahi honge aur creator comment
auto-post nahi hoga.
