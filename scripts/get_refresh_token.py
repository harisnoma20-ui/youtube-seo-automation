"""
OAuth Refresh Token Generator (FIXED VERSION)
-------------------------------------------------------------------
Ye script aapke apne PC/laptop par chalani hai (GitHub Actions par nahi).
Browser khulega, aap apne Google account se login karke permission denge,
aur aakhir mein values print hongi jo GitHub Secrets mein daalni hain.

Is version mein fixes:
  - access_type="offline" + prompt="consent" -> har baar NAYA refresh token
    milta hai (pehle kabhi kabhi refresh_token None aa jata tha).
  - Agar refresh token na mile to saaf error aata hai.
  - Kisi aur credentials file ka path dene ka option (--client-file).
  - Purana galat comment hata diya ("hamesha kaam karega" sahi nahi tha).

SETUP:
  1. Google Cloud Console mein ye APIs enable hon:
     - YouTube Data API v3
     - YouTube Analytics API
     - Google Drive API
  2. Credentials -> OAuth client ID -> "Desktop app" banao, JSON download karke
     isi folder mein "credentials.json" naam se rakho.
  3. OAuth consent screen (Audience) ka status "In production" ho
     (Testing mode mein refresh token 7 din mein expire ho jata hai).
  4. Purani token.json ya purana token delete kar do.
  5. pip install google-auth-oauthlib
  6. python get_refresh_token.py --mode youtube
  7. Browser mein WOHI Google account/brand channel chuno jis par channel hai.
  8. "Google hasn't verified this app" aaye to Advanced -> Go to app (unsafe).
  9. Saari permissions allow karo (checkbox pure select hon).
  10. Print hui values GitHub Secrets mein update karo.

IMPORTANT:
  - Printed secrets kisi ko share mat karo aur public repo mein na daalo.
  - Ek hi refresh token GitHub Secret mein rakho; baar baar naye tokens
    banane se purane tokens invalid ho sakte hain.
  - Token tab bhi invalid ho sakta hai jab aap password badlen, access
    revoke karen, ya app dobara Testing mode mein chali jaye.
"""

import argparse
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("youtube", "drive", "all"),
        default="all",
        help="Brand channels youtube mode use karein; owner Gmail drive mode.",
    )
    parser.add_argument(
        "--client-file",
        default="credentials.json",
        help="OAuth client secrets JSON ka path (default: credentials.json)",
    )
    args = parser.parse_args()

    if args.mode == "youtube":
        scopes = YOUTUBE_SCOPES
    elif args.mode == "drive":
        scopes = DRIVE_SCOPES
    else:
        scopes = YOUTUBE_SCOPES + DRIVE_SCOPES

    flow = InstalledAppFlow.from_client_secrets_file(args.client_file, scopes)

    # access_type=offline + prompt=consent = hamesha naya refresh token milega
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    if not creds.refresh_token:
        print("\nERROR: Refresh token nahi mila.")
        print("Fix: https://myaccount.google.com/permissions se is app ka")
        print("access remove karein, phir script dobara chalayen.")
        sys.exit(1)

    token_name = (
        "DRIVE_OAUTH_REFRESH_TOKEN"
        if args.mode == "drive"
        else "YOUTUBE_OAUTH_REFRESH_TOKEN"
    )

    print("\n" + "=" * 60)
    print("YE VALUES GITHUB SECRETS MEIN DAAL DEIN (purane replace karke):")
    print("=" * 60)
    print(f"YOUTUBE_OAUTH_CLIENT_ID = {creds.client_id}")
    print(f"YOUTUBE_OAUTH_CLIENT_SECRET = {creds.client_secret}")
    print(f"{token_name} = {creds.refresh_token}")
    print("=" * 60)
    print("\nNOTE: Ye token tab tak chalega jab tak:")
    print("  - app 'In production' rahe,")
    print("  - aap Google access revoke na karein ya password na badlen,")
    print("  - aur aap isi client se bahut zyada naye tokens na banayen.")
    print("Ye values kisi ko share na karein.")


if __name__ == "__main__":
    main()
