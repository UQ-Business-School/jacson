<p align="center">
  <img src="assets/jacson-logo-small.svg" alt="JacSON Logo" width="200"/>
</p>

# JacSON — Overview, Setup & Configuration Guide

Welcome to JacSON: a Javascript and JSON-based scraper and integration tool from UQ Jac Course Profiles into Blackboard Ultra.  
This guide explains everything that must be edited if you're adapting JacSON for another school, faculty, or institution.

## Quick Links

- View code on Github: https://github.com/uqgblaze/jacson
- Live version: https://uqgblaze.github.io/jacson/
  - Assessments preview: https://uqgblaze.github.io/jacson/demo/assessments.html
  - Weekly Activities preview: https://uqgblaze.github.io/jacson/demo/weekly-activities.html
  - Installation instructions: https://uqgblaze.github.io/jacson/demo/install.html

## Overview

JacSON automates the retrieval of learning outcomes, assessment details, and weekly learning activities from the current (non-archived) version of the UQ course profiles website. These outputs can then be used to pre-populate components in Blackboard Ultra using JavaScript, enabling a more efficient course build process for teaching teams and learning designers.

## Key Features

- 🧠 **Course Intelligence**: Parses and extracts structured data such as:
  - Learning Outcomes
  - Assessment Tasks (titles, weights, dates, descriptions)
  - Weekly Activities (topics, outcomes, periods)
- ⛔ **Smart Filtering**: Ignores any links to archived course profiles.
- 📝 **Google Sheets Enabled**: Reads course codes from a central **Google Sheet** and updates scrape status and notes for each course
- 🪵 **Creates logs and buffers**: Uses a local `course-list.csv` file to determine which courses to scrape or ignore.
- 🗃️ **Organized Output**: Saves JSON output in folders by semester code.
- ☁️ **Automatic Cloud Publishing**: Configured to automatically upload JSON results to GitHub repository
- 🧪 **Python-based and extensible**: Designed to be modular and easy to integrate with existing Python or web workflows.
- ✅ **Deploy and copy HTML to any course**: You can then copy and deploy the HTML to **any** course in Blackboard Ultra. It will automatically find the course code and find the scraped JSON file within a document.

## Limitations

- This tool is purpose-built for the **UQ JAC system** and may not generalize to other institutions without significant modification.
- Course profiles need to be written in a standardised format to benefit from this tool.
- The JSON file can only be called within a **document** on Blackboard. **This script does not work at the course-view level.**

---

## 🚀 Getting Started

Here’s how to replicate JacSON from scratch in your school or faculty.

### 1. Download Repo as ZIP file

If you haven't already, download the Repo as a ZIP file. Instructions below assume you've saved it to: `%USERPROFILE%\Documents\JacSON`

### 2. 🐍 Install Python

Make sure Python 3.10 or later is installed.

- [Download Python](https://www.python.org/downloads/)
- During install: ✅ *Add Python to PATH*

Once that is installed, open a command prompt window (CMD.exe, not PowerShell!) and change to the folder: e.g. `cd %USERPROFILE%\Documents\JacSON`

Then install dependencies:

`pip install -r requirements.txt`

- If you get an error about 'pip', that means you need to manually install PIP. Google is your friend!

---

### 3\. 📄 Google Sheet Setup

- See link for template: https://docs.google.com/spreadsheets/d/1y4JfTa76oVyWndfA83bAqeN4XwjbMKyWgOyR60yEzXs/edit?usp=sharing

JacSON expects this layout:

| A (Course Code) | B (Auto) | C (Status) | D (Manual) | E | F (Notes) |
| --- | --- | --- | --- | --- | --- |
| ACCT7804 | TRUE |  |  |  |  |

-   Column B: `TRUE` to auto-run
-   Column C: Status (e.g., Scheduled, Success!, Failure)
-   Column D: If `TRUE`, the course is ignored


---

## Getting your SECRETS ready

### 4\. 🔐 Google Sheets Setup

JacSON reads and writes to a shared Google Sheet. To enable this:

#### a. Create a Service Account:

-   Visit: https://console.cloud.google.com/
-   Create a new project and enable the **Google Sheets API**
-   Generate a Service Account with a JSON key file
-   Share your Sheet with the service account email (e.g., `jacson-api@your-project.iam.gserviceaccount.com`)

#### b. Save the key file

Place your credentials JSON here:

`./secrets/credentials.json`

- **Currently unsupported feature**: For GitHub Actions, set as an environment variable `GOOGLE_SERVICE_ACCOUNT_JSON`.

### 🔐 How to Set Up a GitHub Personal Access Token

#### 🧱 Prerequisites

-   A GitHub account
-   Access to the target GitHub repository (owner or write access)
* * *

#### ✅ Step-by-Step Instructions

##### **a\. Log in to GitHub**

Go to: [https://github.com/login](https://github.com/login)

* * *

##### **b\. Open Developer Settings**

-   Click your profile icon in the top-right
-   Select **"Settings"**
-   Scroll down the left sidebar to **"Developer settings"**
-   Click on **"Personal access tokens"**
-   Then click **"Tokens (classic)"**
* * *

##### **c\. Generate a New Token**

-   Click **"Generate new token" → "Generate new token (classic)"**
* * *

##### **d\. Configure the Token**

Fill out the form:

-   **Note**: Something like `JacSON Uploader`
-   **Expiration**: Choose a long-lived token if you're automating
-   **Scopes**: ✅ Tick only:
    -   `repo` → full control of private repositories

This includes:

-   `repo:status`
-   `repo_deployment`
-   `public_repo`
-   `repo:invite`
* * *

##### **e\. Generate and Save the Token**

-   Click the green **"Generate token"** button
-   📋 **Copy and Save the token immediately** — GitHub will not show it again!
* * *

### 🔒 Using the Token in JacSON

1.  Open your JacSON folder.
2.  Create a file:

    `./secrets/github_token.txt`

3.  Paste the token into the file:

    `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX`

✔️ Now JacSON’s `upload_profiles.py` will authenticate and upload `.json`


---

## 🛠 Manual Controls

-   To **test specific courses**: edit `course-list.csv` directly
-   To **run individual scripts**:
    -   Pull course list: `python scripts/generate_course_list.py`
    -   Scrape only: `python jacson.py`
    -   Upload only: `python scripts/upload_profiles.py`
    -   Update status:

---

## Automated Controls

- To run this automatically from your computer, run either option depending on your operating system:

## ✅ Option 1: **Windows** — Use Task Scheduler

### 🔧 Script File (Windows Batch Script)

Save this as `run_jacson.bat` in the same folder as your JacSON project:

`@echo off cd /d "C:\Path\To\Your\JacSON" python scraper_runner.py`

> 🔄 Replace `C:\Path\To\Your\JacSON` with your actual folder path.

* * *

### 📅 Setup in Task Scheduler

1.  Open **Task Scheduler**
2.  Click **Create Basic Task**
3.  Name it: `Run JacSON Scraper`
4.  Choose **Daily**
5.  Set your time (e.g., 9:00 PM)
6.  Action: **Start a program**
7.  Program/script: `C:\Path\To\Your\JacSON\run_jacson.bat`
8.  Finish ✅

* * *

## ✅ Option 2: **macOS / Linux** — Use Cron

### 🔧 Script File

Save this as `run_jacson.sh` and make it executable:

`#!/bin/bash cd /path/to/your/JacSON /usr/bin/python3 scraper_runner.py`

> Use `which python3` to confirm the Python path

Then make it executable:

`chmod +x run_jacson.sh`

* * *

### 📅 Setup Cron Job

1.  Open terminal
2.  Edit your crontab:

    `crontab -e`

3.  Add a line like this (for 9:00 PM daily):

    `0 21 * * * /path/to/your/JacSON/run_jacson.sh >> /path/to/your/JacSON/logs/cron.log 2>&1`

---

# 🔧 Editable Configuration Overview

Below is a complete list of files, variables, and settings that you will need to modify to get JacSON running in your own environment.

---

### 1. ✅ Google Sheets Configuration

**File:** `scripts/sheets_updater.py`  
**Lines:**
```python
SPREADSHEET_ID = '1tJ04EY1AtyS-7iKlmgZhmom0f97xK3DsZ88wkqmRwNs'
RANGE_NAME     = 'Sheet1!A2:F'
CREDENTIALS_FILE = os.path.join('secrets', 'credentials.json')
```

- 🔄 Replace `SPREADSHEET_ID` with your own Google Sheet ID (found in the URL).
- 🔄 Update `RANGE_NAME` if your data starts in a different cell.
- 📁 Ensure `credentials.json` exists at `./secrets/credentials.json`.

---

### 2. 🔐 Google Service Account Setup

**Files:**  
- `scripts/sheets_updater.py`  
- `scripts/update_status.py`  
- `scripts/generate_course_list.py`

These scripts expect a service account credential file saved to:
```bash
./secrets/credentials.json
```

---

### 3. ☁️ GitHub Repository Settings

**File:** `scripts/upload_profiles.py`  
**Lines:**
```python
GITHUB_OWNER = "uqgblaze"
GITHUB_REPO  = "jacson"
```

- 🔄 Replace with your GitHub username/org and repository name.

---

### 4. 🔑 GitHub Personal Access Token

**File:** `scripts/upload_profiles.py`  
**Line:**
```python
TOKEN_PATH = os.path.join(PROJECT_ROOT, "secrets", "github_token.txt")
```

- 🔄 Store your GitHub token in this path as a plain text file (no newline).

---

### 5. 🧾 Google Sheet Column Logic

All Google Sheets integrations assume:
- Column A = Course Code
- Column B = Auto-run checkbox
- Column C = Status (e.g., Scheduled, Success!, Failure)
- Column D = Manual flag (exclusion)
- Column F = Notes

🔄 Adjust in scripts if your Sheet layout differs.

---

### 6. 📄 Target Scraping Domain

**File:** `jacson.py`  
**Line:**
```python
target_domain = "https://course-profiles.uq.edu.au/course-profiles/"
```

- 🔄 Replace with your institution’s profile system root URL.

---

### 7. 📁 Output File Structure

**File:** `jacson.py` → inside `save_course_data()`  
**Line:**
```python
profiles_root = os.path.join(base_directory, "profiles")
```

- 🔄 Change directory if you want to save files somewhere else.

---

### 8. 📋 CSV Filename

**Files:** `jacson.py`, `generate_course_list.py`, `sheets_updater.py`

- 🔄 The file `course-list.csv` is read and written by many scripts. You may rename it, but update all references.

---

### 9. 🕒 GitHub Action Schedule (Optional)

**File:** `.github/workflows/run-jacson.yml`  
**Line:**
```yaml
cron: '0 17 * * *'  # 3:00 AM AEST
```

- 🔄 Update if you want a different automation time or remove schedule entirely.

---

## 📦 Summary Table

| What to Change               | File(s)                       | Location/Note                                  |
|-----------------------------|-------------------------------|-------------------------------------------------|
| Google Sheets ID            | `sheets_updater.py`           | `SPREADSHEET_ID`                               |
| Sheets API credentials      | All Google-related scripts    | Path: `./secrets/credentials.json`             |
| GitHub repo details         | `upload_profiles.py`          | `GITHUB_OWNER`, `GITHUB_REPO`                  |
| GitHub token                | `upload_profiles.py`          | `./secrets/github_token.txt`                   |
| Course sheet column logic   | Sheets-related scripts        | B = Auto, C = Status, D = Manual, F = Notes    |
| Target scrape domain        | `jacson.py`                   | Inside `get_course_profile_links()`            |
| Output folder               | `jacson.py`                   | Inside `save_course_data()`                    |
| CSV filename                | Most scripts                  | `course-list.csv`                              |
| GitHub Action schedule      | `run-jacson.yml`              | `cron:` section                                |

---

## 🙏 Credits

JacSON was built by the UQ Business School Learning Design team with both love 💖 and spite 🤬 for Ultra's Assessment Overview tables. Here's to never needing to manually update those tables ever again!
- Lead developers: **Geoffrey Blazer** and **Bee Hughes**
- With thanks to **Carrie Finn** for letting us cook.
