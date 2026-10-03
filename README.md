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
