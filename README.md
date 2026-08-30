# youtube-seo-automation
Automated SEO system for my YouTube channel
[README.md](https://github.com/user-attachments/files/31614892/README.md)
# YouTube Auto-SEO System — 100% FREE Version

Koi VPS, koi paid AI, koi hosting cost nahi. Poora system free tools pe chalega:

| Kaam | Free Tool |
|---|---|
| Scheduling (khud chalna) | GitHub Actions |
| Trending keywords | Google Trends (pytrends library) |
| SEO content generation | Groq API (free tier, Llama model) |
| YouTube update | YouTube Data API v3 (free) |

---

## Ye Kaam Kaise Karega

1. GitHub Actions har 3 din baad khud is script ko chalayega (aapka laptop off ho tab bhi)
2. Script Google Trends se aapki niche (jo bhi channel type ho) ke trending keywords nikalega
3. Groq AI (free) se un keywords ke hisab se title/description/tags generate karega
4. Aapke channel ki recent videos ka SEO khud update kar dega

---

## Setup Steps

### 1. GitHub Account + Repository
- GitHub.com pe free account banayein (agar nahi hai)
- Ek naya **private repository** banayein (e.g. "youtube-seo-bot")
- Is folder ke sab files (`.github/workflows/`, `scripts/`) us repo mein upload kar dein

### 2. Groq API Key (Free)
- https://console.groq.com pe jayein, free sign up karein
- "API Keys" section se ek key generate karein — bilkul free hai, credit card nahi chahiye

### 3. GitHub Secrets Add Karna
Repo ke andar: **Settings → Secrets and variables → Actions → New repository secret**

Ye secrets add karein:
- `GROQ_API_KEY` → Groq se mili key
- `YOUTUBE_API_KEY` → (channel banne ke baad, Google Cloud Console se)
- `YOUTUBE_CHANNEL_ID` → (channel banne ke baad)

### 4. Test Run
- Repo ke "Actions" tab mein jayein
- "YouTube Auto-SEO System" workflow select karein
- "Run workflow" button se manually ek dafa chala ke test kar sakte hain (channel/YouTube keys ke bina bhi — sirf research + generation test hoga)

---

## Zaroori Baat: YouTube Update Ke Liye OAuth

Filhaal script mein sirf **API key** use hui hai jo YouTube se "padhne" (read) ke liye kaafi hai (jaise recent videos dhoondna). Lekin video ka title/description **update karna** (likhna/write) ke liye YouTube ek zyada secure tareeka mangta hai jise **OAuth2** kehte hain — matlab aapko ek dafa apne Google account se "permission allow" karni padegi (jaise jab koi app aapse "Sign in with Google" karwati hai).

Ye step channel banne ke baad karenge — main us waqt is exact process ko bhi guide kar dunga. Abhi ke liye research + AI-generation wala hissa bilkul test ho sakta hai.

---

## Abhi Kya Test Kar Sakte Hain

Channel/YouTube keys ke bina bhi, aap:
1. GitHub repo bana ke
2. Sirf `GROQ_API_KEY` secret daal ke
3. "Run workflow" dabayein

Aapko "Actions" tab ke logs mein trending keywords + generated title/description/tags dikh jayenge — matlab engine already kaam kar raha hai, sirf YouTube se connect hona baaki hai.

---

## Agla Step

Channel ban jaye to bata dein — phir hum:
1. YouTube API + OAuth setup karenge (Google Cloud Console, click-by-click guide)
2. Real videos pe test update karenge

---

## US/UK Audience Targeting

Ab system US aur UK dono se trending keywords research karta hai (alag alag, phir merge), aur AI ko batata hai ke SEO content usi audience ki language/style mein banaye (American/British English, unke relevant references).

Config (workflow file mein already set hai):
- `TARGET_AUDIENCE_GEOS`: "US,GB" (Google Trends geo codes)
- `TARGET_AUDIENCE_LABEL`: "US and UK" (AI ko diya jaane wala audience description)

Chahen to koi ek country (e.g. sirf "US") ya kisi aur country ka geo code daal ke bhi target kar sakte hain.

---

## 6 Advanced Growth Features (growth_features.py)

1. **Weekly Summary Report** — har Monday, poore channel ka growth trend (best/worst video, total views, average CTR) WhatsApp pe aata hai.

2. **Trending Surge Alert** — agar koi niche keyword achanak spike kare (Google Trends data), turant alert mil jata hai, 3-din wale cron ka wait nahi karna padta.

3. **Keyword Learning Loop** — jin videos ki CTR achi hoti hai, unke tags `winning_keywords.json` mein save ho kar future SEO generation mein prioritize hote hain. Ye file bhi tracking sheet ki tarah repo mein commit hoti hai.

4. **Community Post Ideas** — AI 2 chhote post ideas generate karta hai, WhatsApp pe bhejta hai. **NOTE:** YouTube API Community tab pe post karna support nahi karti, is liye posting manual karni hogi.

5. **Auto Pinned Comment** — system ek engaging comment generate karke khud post kar deta hai (channel owner ki taraf se). **NOTE:** Comment ko PIN karna YouTube API support nahi karti — post ho jayega, pin karna aapko YouTube Studio mein ek click se khud karna hoga. `ENABLE_AUTO_COMMENT` secret ko "false" karke isay band bhi kar sakte hain.

6. **Competitor Tracking** — niche ke pichle 14 din ke top-viewed videos (kisi bhi channel ke) ke titles dikhata hai, taake pata chale abhi kis type ke titles trend mein hain.

---

## Video Upload Automation (Drive → YouTube)

Ab system nayi videos khud upload bhi kar sakta hai — bas Google Drive ke ek folder mein daal dein:

### Setup

1. Google Drive mein 2 folders banayein: **"ToUpload"** aur **"Uploaded"**
2. Dono folders ke Drive URL se **Folder ID** nikal lein (URL mein `folders/` ke baad wala hissa)
3. GitHub Secrets mein add karein:
   - `DRIVE_TO_UPLOAD_FOLDER_ID`
   - `DRIVE_UPLOADED_FOLDER_ID`
4. Apni ready videos (voice ke sath) **"ToUpload"** folder mein daal dein — kahin se bhi, phone se bhi

### Kya Hoga

Har run pe system "ToUpload" folder check karega, nayi video mile to:
1. Uska AI se SEO (title/description/tags) generate karega
2. YouTube pe upload kar dega
3. File ko "Uploaded" folder mein move kar dega (taake dobara upload na ho)
4. WhatsApp pe confirm kar dega

## OAuth Refresh Token Kaise Nikalein (Zaroori, Ek Dafa)

`scripts/get_refresh_token.py` ko apne PC pe (GitHub Actions pe NAHI) chalana hai:

1. Google Cloud Console mein OAuth Client ID banayein (type: Desktop app), download kar ke isi folder mein `credentials.json` naam se save karein
2. `pip install google-auth-oauthlib`
3. `python scripts/get_refresh_token.py`
4. Browser khulega, Google account se login/allow karein
5. Terminal mein 3 values print hongi — inhe GitHub Secrets mein daal dein: `YOUTUBE_OAUTH_CLIENT_ID`, `YOUTUBE_OAUTH_CLIENT_SECRET`, `YOUTUBE_OAUTH_REFRESH_TOKEN`

Ye ek dafa karna hai, dobara zarurat nahi padegi.

---

## Upload Calendar (Kaunsi Video Kab)

System ab pehle se decide kiye gaye din ke hisab se upload karta hai:

| Din | Kya Upload Hoga |
|---|---|
| Monday - Friday | Ek Short (5 hook Shorts ka plan isi se match karta hai) |
| Saturday | Full/Long video |
| Sunday | Rest day, koi upload nahi |

Iske liye 4 Drive folders chahiye, aur secrets mein unke IDs:
- `DRIVE_SHORTS_TOUPLOAD_FOLDER_ID` / `DRIVE_SHORTS_UPLOADED_FOLDER_ID`
- `DRIVE_LONG_TOUPLOAD_FOLDER_ID` / `DRIVE_LONG_UPLOADED_FOLDER_ID`

Calendar khud customize kar sakte hain — `SHORTS_UPLOAD_DAYS` aur `LONG_UPLOAD_DAYS` secrets mein comma-separated weekday numbers dein (Monday=0 ... Sunday=6).

**Note:** Workflow ab DAILY chalta hai (taake calendar roz check ho sake), lekin existing-videos ka SEO-refresh (metadata update) andar hi andar sirf har 3 din chalta hai — script khud ye manage karti hai, koi extra setup nahi chahiye.

## Hashtags

Ab AI title/description/tags ke sath 3-5 relevant **hashtags** bhi generate karta hai, jo description ke end mein automatically add ho jate hain. Shorts ke liye hashtags mein `#Shorts` zaroor shamil hota hai — YouTube isay dekh kar video ko Shorts shelf mein dikhata hai.

---

## High-CPM Country Targeting (Views ki Bajaye Earning Optimize Karna)

System ab sirf "views" ke liye nahi, **highest CPM (per-view earning) wale countries** ke liye optimize karta hai. 2026 data ke mutabiq: Australia (~$36 CPM), USA (~$32), Canada (~$30), Switzerland (~$25), UK (~$20), Norway (~$18) sabse zyada paying markets hain — India jaise countries ke muqable 20x tak zyada.

Default `TARGET_AUDIENCE_GEOS`: "US,AU,CA,GB,CH,NO" — chahen to is list ko customize kar sakte hain.

## Scheduled Publish Time (Peak Time Pe Video Public Hona)

Video upload turant ho jati hai, lekin **PUBLIC sirf sahi time pe** hoti hai (YouTube ka "Scheduled Publish" feature use karke). Default: `PUBLISH_HOUR_UTC = 21` (21:00 UTC) — ye US Eastern ke early evening (~5pm) aur UK/Europe ke evening (~9-10pm) ke beech ka reasonable compromise hai, kyunke in dono regions ka perfect overlap possible nahi (5+ ghante ka time-zone farak hai).

Chahen to `PUBLISH_HOUR_UTC` secret change kar ke apni audience ke hisab se adjust kar sakte hain.

---

## 3 Final Quality Features (quality_features.py)

1. **Thumbnail Issue Notification (NOT auto-change)** — Agar diagnosis mein THUMBNAIL issue REPEAT ho (escalation), system sirf ek clear "ACTION NEEDED" alert WhatsApp pe bhejta hai — thumbnail khud nahi badalta. Ye jaan-boojh kar manual rakha gaya hai (creator apni marzi se thumbnail badalna chahta hai, automation se nahi). Thumbnail generation ka code (`generate_thumbnail`, `generate_thumbnail_from_video` frame-extraction ke sath) module mein maujood hai agar future mein kabhi enable karna ho, lekin filhaal system isay call nahi karta.

2. **Caption Improvement** — YouTube khud video upload hone ke baad auto-captions (ASR) banata hai. System unhe nikaal kar AI se punctuation/clarity behtar karta hai aur ek naya "Improved" caption track upload kar deta hai. **NOTE:** Ye YouTube ke apne auto-captions ko behtar karta hai, scratch se transcript nahi banata (kyunke humein actual audio transcript nahi milta). `ENABLE_CAPTION_IMPROVEMENT` secret se control hota hai.

3. **Quota Safety** — YouTube Data API ki daily limit 10,000 units hoti hai. System har operation ki estimated cost track karta hai, aur agar `QUOTA_SAFETY_LIMIT` (default 9000) ke paas pahunch jaye, to non-critical operations (competitor tracking, comments) khud skip kar deta hai taake critical operations (SEO update, upload) hamesha successful rahein. Har WhatsApp report mein quota status bhi aata hai.
