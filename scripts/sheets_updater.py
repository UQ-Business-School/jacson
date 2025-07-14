import os
import csv
import logging
from datetime import datetime

import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SPREADSHEET_ID    = '1tJ04EY1AtyS-7iKlmgZhmom0f97xK3DsZ88wkqmRwNs'
FETCH_RANGE       = 'Sheet1!A4:F'    # used by fetch_course_list
CODE_RANGE        = 'Sheet1!A4:A'    # used by update_status_sheet
START_ROW         = 4                # first row of CODE_RANGE
SCOPES            = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE  = os.path.join('secrets', 'credentials.json')
# ────────────────────────────────────────────────────────────────────────────────
# URL to existing list: https://docs.google.com/spreadsheets/d/1tJ04EY1AtyS-7iKlmgZhmom0f97xK3DsZ88wkqmRwNs/edit?usp=sharing

def get_service():
    """
    Build & return a Google Sheets v4 service, with discovery cache disabled
    (avoids the oauth2client<4.0.0 warning).
    """
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    return service


def fetch_course_list(csv_output='course-list.csv'):
    """
    Pull course codes from columns A, B and D of the sheet and write out
    'included' vs 'excluded' lists to a local CSV.
    """
    service = get_service()
    sheet   = service.spreadsheets()
    result  = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=FETCH_RANGE
    ).execute()
    values = result.get('values', [])

    included = []
    excluded = []
    for row in values:
        code        = row[0].strip() if len(row) > 0 else ''
        auto_flag   = row[1].strip().lower() if len(row) > 1 else ''
        manual_flag = row[3].strip().lower() if len(row) > 3 else ''
        if auto_flag == 'true':
            included.append(code)
        elif manual_flag == 'true':
            excluded.append(code)

    # write CSV with two columns: included / excluded
    with open(csv_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['included', 'excluded'])
        for i in range(max(len(included), len(excluded))):
            writer.writerow([
                included[i] if i < len(included) else '',
                excluded[i] if i < len(excluded) else '',
            ])

    logging.info(f"Fetched {len(included)} included and {len(excluded)} excluded courses.")


def update_status_sheet(scrape_results):
    """
    For each course in scrape_results, find its row in column A and update:
      • Column B → unchecked (False)
      • Column C → "Success!" or "Error"
      • Column F → timestamped note or error message
    Leaves all other rows untouched.
    """
    service = get_service().spreadsheets()

    # timezone and timestamp
    tz    = pytz.timezone('Australia/Brisbane')
    now   = datetime.now(tz)
    stamp = now.strftime('%d %B, %Y at %H:%M') + ' AEST'

    try:
        # 1) Read column A codes from row 4 down
        resp  = service.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=CODE_RANGE
        ).execute()
    except HttpError as e:
        logging.error(f"Failed to read course codes: {e}")
        raise

    rows = resp.get('values', [])
    if not rows:
        logging.info("No course codes found in sheet; nothing to update.")
        return

    # 2) Build a batch of single-cell updates for only matching codes
    updates = []
    for idx, row in enumerate(rows, start=START_ROW):
        code = row[0].strip() if row else ''
        if code not in scrape_results:
            continue

        result = scrape_results[code]
        ok     = result.get('success', False)
        status = 'Success!' if ok else 'Error'
        note   = (f"Successfully ran on {stamp}"
                  if ok else result.get('note', 'Unknown error'))

        # schedule single-cell writes
        updates.extend([
            { 'range': f'Sheet1!B{idx}', 'values': [[False]] },
            { 'range': f'Sheet1!C{idx}', 'values': [[status]] },
            { 'range': f'Sheet1!F{idx}', 'values': [[note]] }
        ])

    if not updates:
        logging.info("No matching course codes to update; exiting.")
        return

    body = {
        'valueInputOption': 'RAW',
        'data': updates
    }

    try:
        service.values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        logging.info(f"Updated {len(updates)//3} course rows on the sheet.")
    except HttpError as e:
        logging.error(f"Failed to write updates: {e}")
        raise
