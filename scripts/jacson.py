import requests
from bs4 import BeautifulSoup
import re
import json
import os
import csv
import time
from urllib.parse import urljoin, urlparse
from bs4.element import NavigableString

def markdownify_html(elem):
    """
    Convert a BeautifulSoup element to markdown-compatible HTML by preserving inline formatting.
    """
    if elem:
        return str(elem).strip()
    return None

def extract_course_codes(full_course_code):
    parts = full_course_code.split('-')
    return {
        "course_code": parts[0],
        "class_code": parts[1],
        "semester_code": parts[2]
    }

def extract_full_course_code(soup):
    breadcrumb_link = soup.find('a', href=re.compile('/course-profiles/.*'))
    if breadcrumb_link:
        full_course_code = breadcrumb_link['href'].split('/')[-1]
        return full_course_code
    return None

def extract_course_header_info(soup):
    """
    Extracts course_title, study_period, location, and attendance from the hero banner.
    """
    header = soup.find('div', class_='hero__text')
    course_title = study_period = location = attendance = None

    if header:
        h1 = header.find('h1')
        if h1:
            full_title = h1.get_text(strip=True)
            course_title = re.sub(r'\s*\([^)]+\)$', '', full_title)

        dl = header.find('dl', class_='hero__course-offerings')
        if dl:
            for div in dl.find_all('div', class_='hero__course-offering'):
                label = div.find('dt')
                value = div.find('dd')
                if not label or not value:
                    continue
                label_text = label.get_text(strip=True).lower()
                value_text = value.get_text(strip=True)

                if label_text == 'study period':
                    study_period = value_text
                elif label_text == 'location':
                    location = value_text
                elif label_text == 'attendance mode':
                    attendance = value_text

    return {
        "course_title": course_title,
        "study_period": study_period,
        "location": location,
        "attendance": attendance
    }

def extract_special_indicators(detail):
    indicators = []
    ul = detail.find_next('ul', class_='icon-list')
    if ul:
        for li in ul.find_all('li'):
            indicator_class = li.get('class', [])
            indicator_text = li.get_text(strip=True)
            indicators.append({
                "special_indicators_class": ' '.join(indicator_class),
                "special_indicator_text": indicator_text
            })
    return indicators

def extract_learning_outcomes(soup):
    outcomes = []
    lo_section = soup.find('section', id='learning-outcomes')
    if lo_section:
        for wrapper in lo_section.find_all('div', class_='learning-outcome-wrapper'):
            for outcome in wrapper.find_all('p'):
                strong_tag = outcome.find('strong', class_='text--primary')
                if strong_tag:
                    number = strong_tag.get_text(strip=True)
                    description = outcome.get_text(strip=True).replace(number, '').strip()
                    outcomes.append({"number": number, "description": description})
    return outcomes

def extract_assessment_details(soup):
    details_section = soup.find('section', id='assessment-details')
    details = []
    if details_section:
        for detail in details_section.find_all('h3', id=re.compile('^assessment-detail-')):
            assessment = {
                "assessment_detail_section_id": detail.get('id', ""),
                "assessment_title": detail.get_text(strip=True),
                "special_indicators": extract_special_indicators(detail),
                "weighting": markdownify_html(detail.find_next('dt', string='Weight').find_next('dd')) if detail.find_next('dt', string='Weight') else None,
                "due_date": markdownify_html(detail.find_next('dt', string='Due date').find_next('dd')) if detail.find_next('dt', string='Due date') else None,
                "learning_objectives": detail.find_next('dt', string='Learning outcomes').find_next('dd').get_text(strip=True) if detail.find_next('dt', string='Learning outcomes') else None,
                "mode": detail.find_next('dt', string='Mode').find_next('dd').get_text(strip=True) if detail.find_next('dt', string='Mode') else None,
                "category": detail.find_next('dt', string='Category').find_next('dd').get_text(strip=True) if detail.find_next('dt', string='Category') else None,
                "task_description": markdownify_html(detail.find_next('h4', string='Task description').find_next('div', class_='collapsible')) if detail.find_next('h4', string='Task description') else None,
                "submission_guidelines": markdownify_html(detail.find_next('h4', string='Submission guidelines').find_next('p')) if detail.find_next('h4', string='Submission guidelines') else None,
                "deferral_or_extension": markdownify_html(detail.find_next('h5', string='Deferral or extension').find_next('p')) if detail.find_next('h5', string='Deferral or extension') else None,
                "late_submission": markdownify_html(detail.find_next('h5', string='Late submission').find_next('p')) if detail.find_next('h5', string='Late submission') else None,
                "additional_info": markdownify_html(detail.find_next('h5', string=re.compile('.*')).find_next('p')) if detail.find_next('h5', string=re.compile('.*')) else None
            }
            details.append(assessment)
    return details

def extract_learning_activities(soup):
    activities = []
    table = soup.find('table', id='table-to-filter')
    if table:
        tbody = table.find('tbody')
        if tbody:
            current_learning_period = None
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                
                # Check if this row has a learning period cell (first cell with course-table__new-group class)
                if len(cells) >= 3 and cells[0].has_attr('class') and 'course-table__new-group' in cells[0].get('class', []):
                    # This row starts a new learning period
                    current_learning_period = cells[0].get_text(strip=True)
                    activity_type = cells[1].get_text(strip=True)
                    topic_cell = cells[2]
                elif len(cells) >= 2:
                    # This row continues the current learning period
                    # The first cell is activity type, second is topic
                    activity_type = cells[0].get_text(strip=True)
                    topic_cell = cells[1]
                else:
                    continue
                
                # Extract topic information with markdownify_html
                topic = markdownify_html(topic_cell)
                topic_title = ""
                topic_description = ""
                learning_outcomes = []

                div_element = topic_cell.find('div')
                if div_element:
                    # Extract the first strong element as title
                    first_strong = div_element.find('strong')
                    if first_strong:
                        topic_title = markdownify_html(first_strong)
                    
                    # Get all text content for processing
                    full_text = div_element.get_text(" ", strip=True)
                    
                    # Split by learning outcomes
                    parts = re.split(r'(?:Learning outcomes?|LO):\s*', full_text, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        topic_description = markdownify_html(parts[0].strip())
                        outcomes_text = parts[1].strip()
                        # Parse learning outcomes
                        outcomes_list = re.split(r'[,;]\s*|\s+and\s+', outcomes_text)
                        learning_outcomes = [outcome.strip() for outcome in outcomes_list if outcome.strip()]
                    else:
                        topic_description = markdownify_html(full_text)

                # Only add if we have valid data
                if current_learning_period and activity_type and topic:
                    activities.append({
                        "learning_period": current_learning_period,
                        "activity_type": activity_type,
                        "topic": topic,
                        "topic_title": topic_title,
                        "topic_description": topic_description,
                        "learning_outcomes": learning_outcomes
                    })
    return activities

def extract_semester_details(soup):
    summary_table = soup.find('section', id='course-overview--section').find('dl')
    if summary_table:
        study_period = summary_table.find('dd').get_text(strip=True)
        return study_period
    return None

def get_course_profile_links(course_code):
    search_url = f"https://programs-courses.uq.edu.au/course.html?course_code={course_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        profile_links = []
        target_domain = "https://course-profiles.uq.edu.au/course-profiles/"
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('http'):
                href = urljoin(search_url, href)
            if href.startswith(target_domain):
                profile_links.append(href)
            elif 'archive.course-profiles.uq.edu.au' in href:
                print(f"  Skipping archived profile: {href}")
        return profile_links
    except requests.RequestException as e:
        print(f"Error fetching course search page for {course_code}: {e}")
        return []

def process_course_profile(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        full_course_code = extract_full_course_code(soup)
        course_codes = extract_course_codes(full_course_code) if full_course_code else {}
        semester_details = extract_semester_details(soup)
        assessments = extract_assessment_details(soup)
        learning_outcomes = extract_learning_outcomes(soup)
        learning_activities = extract_learning_activities(soup)
        header_info = extract_course_header_info(soup)

        output = {
            **header_info,
            "url": url,
            "full_course_code": full_course_code,
            **course_codes,
            "semester_details": semester_details,
            "learning_outcomes": learning_outcomes,
            "assessments": assessments,
            "learning_activities": learning_activities
        }
        return output
    except requests.RequestException as e:
        print(f"Error processing course profile {url}: {e}")
        return None

import os
import json

def save_course_data(course_data, base_directory="."):
    """
    Save course_data as JSON under:
      {base_directory}/profiles/{semester_code}/{full_course_code}.json

    Returns True on success, False otherwise.
    """
    if not course_data or not course_data.get("full_course_code"):
        return False

    full_course_code = course_data["full_course_code"]
    semester_code    = course_data.get("semester_code", "").strip()

    # build: ./profiles/{semester_code}
    profiles_root = os.path.join(base_directory, "profiles")
    semester_dir  = os.path.join(profiles_root, semester_code)
    os.makedirs(semester_dir, exist_ok=True)

    filename = f"{full_course_code}.json"
    filepath = os.path.join(semester_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(course_data, f, ensure_ascii=False, indent=4)
        print(f"Saved data to {filepath}")
        return True

    except Exception as e:
        print(f"Error saving data to {filepath}: {e}")
        return False


def load_course_list(csv_filename="course-list.csv"):
    included_courses = []
    excluded_courses = []
    if not os.path.exists(csv_filename):
        print(f"CSV file {csv_filename} not found. Creating sample file...")
        create_sample_csv(csv_filename)
        return included_courses, excluded_courses
    try:
        with open(csv_filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            first_row = next(reader, None)
            if first_row and (first_row[0].lower() == 'included' or first_row[0].lower() == 'course_code'):
                pass
            else:
                if first_row and len(first_row) >= 2:
                    if first_row[0].strip():
                        included_courses.append(first_row[0].strip())
                    if first_row[1].strip():
                        excluded_courses.append(first_row[1].strip())
            for row in reader:
                if len(row) >= 2:
                    if row[0].strip():
                        included_courses.append(row[0].strip())
                    if row[1].strip():
                        excluded_courses.append(row[1].strip())
        print(f"Loaded {len(included_courses)} courses to include and {len(excluded_courses)} courses to exclude")
        return included_courses, excluded_courses
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return [], []

def create_sample_csv(filename="course-list.csv"):
    demo_courses = ["ACCT7804", "BISM7808", "ECON7012"]
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["included", "excluded"])
            for course in demo_courses:
                writer.writerow([course, ""])
            for _ in range(5):
                writer.writerow(["", ""])
        print(f"Created sample CSV file: {filename}")
    except Exception as e:
        print(f"Error creating sample CSV file: {e}")

def main():
    print("Starting course profile scraper...")
    included_courses, excluded_courses = load_course_list()
    if not included_courses:
        print("No courses found in the included list. Please check your course-list.csv file.")
        return {}
    print(f"Processing {len(included_courses)} courses...")
    print(f"Excluding {len(excluded_courses)} courses...")
    scrape_results = {}
    for course_code in included_courses:
        if course_code in excluded_courses:
            print(f"Skipping {course_code} (found in excluded list)")
            continue
        print(f"\nProcessing course: {course_code}")
        profile_links = get_course_profile_links(course_code)
        if not profile_links:
            print(f"No current course profile links found for {course_code}")
            scrape_results[course_code] = {"success": False, "note": "No current profile links found"}
            continue
        success = False
        for link in profile_links:
            print(f"Processing: {link}")
            course_data = process_course_profile(link)
            if course_data:
                saved = save_course_data(course_data)
                if saved:
                    success = True
            time.sleep(1)
        scrape_results[course_code] = {
            "success": success,
            "note": "" if success else "Profile found but failed to save"
        }
    print("\nScraping completed!")
    return scrape_results

if __name__ == "__main__":
    main()
