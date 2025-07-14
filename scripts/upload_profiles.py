#!/usr/bin/env python3
# upload_profiles.py
import os
import base64
import json
import requests

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

GITHUB_OWNER = "uqgblaze"   # CHANGE OWNER
GITHUB_REPO  = "jacson"     # if needed, change repo name

# PROJECT ROOT: one directory up from this script
SCRIPT_DIR   = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))

# LOCAL “profiles/” folder (absolute on disk)
BASE_PATH = os.path.join(PROJECT_ROOT, "profiles")

# REPO “profiles” folder (literal, no drive letters)
REPO_BASE = "profiles"

# Your token file lives in ./secrets/github_token.txt at project root
TOKEN_PATH   = os.path.join(PROJECT_ROOT, "secrets", "github_token.txt")

# ──────────────────────────────────────────────────────────────────────────────
# LOAD TOKEN
# ──────────────────────────────────────────────────────────────────────────────

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
# HELPER TO UPLOAD A SINGLE FILE
# ──────────────────────────────────────────────────────────────────────────────

def upload_file(local_path, repo_path):
    """
    Uploads (or updates) a single file to GitHub under repo_path.
    """
    # Read & base64-encode
    with open(local_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()

    # Check if file exists to get its SHA
    get_url = f"{API_ROOT}/{repo_path}"
    r = requests.get(get_url, headers=HEADERS)
    if r.status_code == 200:
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

    # PUT to create/update
    put_url = get_url
    response = requests.put(put_url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code in (200, 201):
        print(f"✅ {action} succeeded: {repo_path}")
    else:
        print(f"❌ {action} failed: {repo_path}")
        print(response.status_code, response.text)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN: walk the profiles/ directory
# ──────────────────────────────────────────────────────────────────────────────

for root, dirs, files in os.walk(BASE_PATH):
    for fn in files:
        local_file = os.path.join(root, fn)

        # rel_path is like "7460/COURSE123.json"
        rel_path = os.path.relpath(local_file, BASE_PATH).replace("\\", "/")

        # repo_path now becomes "profiles/7460/COURSE123.json"
        repo_path = f"{REPO_BASE}/{rel_path}"

        upload_file(local_file, repo_path)
