#### USE THIS CODE TO EXECUTE AND RUN JACSON:
# 1. CREATES LOG, THEN FETCHES COURSES TO SCRAPE FROM GOOGLE SHEETS
# 2. SCRAPES PUBLIC DATA FROM COURSE-PROFILES.UQ.EDU.AU, SAVES LOCALLY UNDER ./PROFILES
# 3. UPLOADS ALL COURSE PROFILES FROM THE LOCAL FILE TO THIS RESPOSITORY
####
# scripts/scraper_runner.py
import os
import time
import logging
import subprocess
from datetime import datetime

# All scripts now live in the same directory (./scripts)
import jacson
import sheets_updater

# Project root is one level up from ./scripts/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
COURSE_CSV_PATH = os.path.join(PROJECT_ROOT, "course-list.csv")
UPLOAD_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "upload_profiles.py")


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"scrape_{datetime.now().strftime('%Y-%m-%d')}.log")
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s [%(levelname)s]: %(message)s',
        level=logging.INFO
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("Logging setup complete.")


def update_course_list_from_google_sheets():
    logging.info("Updating course-list.csv from Google Sheets...")
    sheets_updater.fetch_course_list(COURSE_CSV_PATH)
    logging.info("course-list.csv updated.")


def run_scraper():
    logging.info("Starting JacSON scraper...")
    scrape_results = jacson.main()
    logging.info("JacSON scraper completed.")
    return scrape_results


def upload_profiles():
    logging.info("Uploading profiles via upload_profiles.py...")
    try:
        subprocess.run(["python", UPLOAD_SCRIPT_PATH], check=True)
        logging.info("Profiles uploaded successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"upload_profiles.py failed: {e}")


def update_status_on_sheets(scrape_results):
    logging.info("Updating status on Google Sheets...")
    sheets_updater.update_status_sheet(scrape_results)
    logging.info("Google Sheets status update complete.")


def main():
    setup_logging()
    update_course_list_from_google_sheets()
    scrape_results = run_scraper()
    upload_profiles()
    update_status_on_sheets(scrape_results)
    logging.info("All tasks completed. Script finished.")


if __name__ == "__main__":
    main()
