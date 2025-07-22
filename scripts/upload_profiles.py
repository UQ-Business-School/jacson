#!/usr/bin/env python3
# upload_profiles.py
import os
import base64
import hashlib
import json
import requests

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

GITHUB_OWNER = "UQ-Business-School" # CHANGE OWNER (Name of username or org name)
GITHUB_REPO  = "jacson"             # if needed, change repo name

SCRIPT_DIR   = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
BASE_PATH    = os.path.join(PROJECT_ROOT, "profiles")
REPO_BASE    = "profiles"
TOKEN_PATH   = os.path.join(PROJECT_ROOT, "secrets", "github_token.txt")

with open(TOKEN_PATH, "r") as f:
    GH_TOKEN = f.read().strip()

if not GH_TOKEN:
    print("⚠️  No token found in", TOKEN_PATH)
    exit(1)

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

API_ROOT = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"

# ──────────────────────────────────────────────────────────────────────────────
# FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def calculate_sha1(content_bytes):
    return hashlib.sha1(content_bytes).hexdigest()

def upload_file(local_path, repo_path):
    with open(local_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    get_url = f"{API_ROOT}/{repo_path}"
    r = requests.get(get_url, headers=HEADERS)

    if r.status_code == 200:
        remote_content = r.json().get("content", "").replace("\n", "")
        remote_sha1 = calculate_sha1(base64.b64decode(remote_content.encode()))
        local_sha1 = calculate_sha1(data)

        if local_sha1 == remote_sha1:
            print(f"⏭️  Skipping (no change): {repo_path}")
            return

        sha = r.json()["sha"]
        action = "Updating"
    elif r.status_code == 404:
        sha = None
        action = "Creating"
    else:
        print(f"❌ Failed to check {repo_path}: {r.status_code} {r.text}")
        return

    payload = {
        "message": f"{action} {repo_path}",
        "content": b64,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(get_url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code in (200, 201):
        print(f"✅ {action} succeeded: {repo_path}")
    else:
        print(f"❌ {action} failed: {repo_path}")
        print(response.status_code, response.text)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────────

for root, dirs, files in os.walk(BASE_PATH):
    for fn in files:
        local_file = os.path.join(root, fn)
        rel_path = os.path.relpath(local_file, BASE_PATH).replace("\\", "/")
        repo_path = f"{REPO_BASE}/{rel_path}"
        upload_file(local_file, repo_path)
