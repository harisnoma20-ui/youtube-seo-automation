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

## Naya channel add karna
1. `channels_config.json` mein naya object add karein, `secret_prefix` jaise `"CH2_"` rakhein
2. GitHub Secrets mein CH2_ prefix wale secrets banayein (YOUTUBE_API_KEY, CHANNEL_ID, OAUTH_*, DRIVE_* folder IDs)
3. `.github/workflows/seo-automation.yml` mein CH2 wala commented block uncomment karein

Setup ke baaki steps PDF guide follow karein.

## Shorts folder rule

`DRIVE_SHORTS_TOUPLOAD_FOLDER_ID` ka folder upload intent batata hai, lekin
YouTube classification force nahi karta. Automation upload se pehle file ko
check karti hai: duration 180 seconds ya kam aur aspect ratio square/vertical
hona zaroori hai. Invalid file upload nahi hoti aur `Uploaded` folder mein move
nahi hoti. 10-minute video ko Short banane ke liye pehle usay 3-minute ya chhote
vertical clips mein export karna hoga.

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
