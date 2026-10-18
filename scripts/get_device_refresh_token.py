"""Generate an OAuth refresh token without a localhost callback."""

import argparse
import json
import time

import requests


YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("youtube", "drive"), required=True)
    args = parser.parse_args()

    with open("device_credentials.json", encoding="utf-8") as handle:
        client = json.load(handle)["installed"]

    scopes = YOUTUBE_SCOPES if args.mode == "youtube" else DRIVE_SCOPES
    response = requests.post(
        "https://oauth2.googleapis.com/device/code",
        data={"client_id": client["client_id"], "scope": " ".join(scopes)},
        timeout=30,
    )
    response.raise_for_status()
    device = response.json()

    print(f"OPEN_URL={device['verification_url']}", flush=True)
    print(f"USER_CODE={device['user_code']}", flush=True)

    interval = int(device.get("interval", 5))
    deadline = time.time() + int(device["expires_in"])
    while time.time() < deadline:
        time.sleep(interval)
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client["client_id"],
                "client_secret": client["client_secret"],
                "device_code": device["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=30,
        )
        payload = token_response.json()
        if token_response.ok:
            name = (
                "YOUTUBE_OAUTH_REFRESH_TOKEN"
                if args.mode == "youtube"
                else "DRIVE_OAUTH_REFRESH_TOKEN"
            )
            print(f"{name}={payload['refresh_token']}", flush=True)
            return
        error = payload.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        raise RuntimeError(payload)

    raise TimeoutError("Device authorization expired; run the script again.")


if __name__ == "__main__":
    main()
