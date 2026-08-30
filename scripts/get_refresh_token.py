"""
Ek-Dafa OAuth Refresh Token Generate Karne Wala Script
-------------------------------------------------------------------
Ye script sirf EK DAFA aapke apne PC/laptop pe chalani hai (GitHub Actions
pe nahi). Ye ek browser window kholegi jahan aap apne Google account se
login/permission allow karenge, aur aakhir mein 3 values print hongi jo
aapko GitHub Secrets mein daalni hain.

SETUP (isko chalane se pehle):
  1. Google Cloud Console (console.cloud.google.com) mein jayein
  2. Naya project banayein (ya purana select karein)
  3. "APIs & Services" -> "Library" mein jayein, ye 3 APIs enable karein:
     - YouTube Data API v3
     - YouTube Analytics API
     - Google Drive API
  4. "APIs & Services" -> "Credentials" -> "Create Credentials" -> "OAuth client ID"
     - Application type: "Desktop app"
     - Naam kuch bhi rakh dein
  5. Bani hui credential ko download karein (JSON file), aur isi folder
     mein "credentials.json" naam se save karein
  6. Terminal mein: pip install google-auth-oauthlib
  7. Terminal mein: python get_refresh_token.py
  8. Browser khulega, apne Google account se login/allow karein
  9. Terminal mein 3 values print hongi — GitHub Secrets mein daal dein:
     YOUTUBE_OAUTH_CLIENT_ID, YOUTUBE_OAUTH_CLIENT_SECRET, YOUTUBE_OAUTH_REFRESH_TOKEN
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/drive",
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("YE 3 VALUES GITHUB SECRETS MEIN DAAL DEIN:")
    print("=" * 60)
    print(f"YOUTUBE_OAUTH_CLIENT_ID = {creds.client_id}")
    print(f"YOUTUBE_OAUTH_CLIENT_SECRET = {creds.client_secret}")
    print(f"YOUTUBE_OAUTH_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)
    print("\nYe refresh token hamesha kaam karega — dobara ye script chalane")
    print("ki zarurat nahi (jab tak aap khud Google account se access revoke na karein).")


if __name__ == "__main__":
    main()
