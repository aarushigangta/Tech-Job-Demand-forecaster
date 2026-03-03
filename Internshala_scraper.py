import time
import random
import re
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# Config 
DEBUG_MODE = "--debug" in sys.argv
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "internshala_jobs.csv")
DEBUG_FILE  = "debug_card.html"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEARCH_ROLES = [
    "python", "data-science", "machine-learning", "web-development",
    "data-analyst", "java", "react", "cloud-computing", "devops",
    "android-development",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://internshala.com/",
}

MAX_PAGES = 5
DELAY_MIN = 2.0
DELAY_MAX = 4.0


# Helpers 

def get_soup(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        print(f" Request failed: {url} → {e}")
        return None


def first_text(*tags) -> str:
    """Return stripped text from the first non-None, non-empty tag."""
    for tag in tags:
        if tag:
            t = tag.get_text(strip=True) if hasattr(tag, "get_text") else str(tag).strip()
            if t:
                return t
    return ""


def parse_relative_date(text: str) -> str:
    text = text.lower().strip()
    today = datetime.today()
    if "today" in text or "just now" in text or "hour" in text:
        return today.strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s*day", text)
    if m:
        return (today - timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s*week", text)
    if m:
        return (today - timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s*month", text)
    if m:
        return (today - timedelta(days=30 * int(m.group(1)))).strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")


#  Debug Mode 

def run_debug():
    """
    Fetches one page, saves the first job card's HTML to debug_card.html,
    and prints every class name + text found inside it.
    Use this output to update the selectors in parse_card() below.
    """
    url = "https://internshala.com/jobs/python-jobs/page-1/"
    print(f"🐛 DEBUG MODE\nFetching: {url}\n")
    soup = get_soup(url)
    if not soup:
        print("Could not fetch page. Check your internet connection.")
        return

    # Try to find any job card
    card = None
    tried = []
    for cls in ["individual_internship", "internship_meta", "job-card",
                "internship-card", "job_card", "listing-container"]:
        card = soup.find("div", class_=cls)
        tried.append(cls)
        if card:
            print(f"Card found with class='{cls}'")
            break

    if not card:
        card = (soup.find("div", attrs={"data-internship_id": True}) or
                soup.find("div", attrs={"data-job_id": True}))
        if card:
            print(" Card found via data attribute")

    if not card:
        print(f" No card found with tried classes: {tried}")
        print("Saving FULL page HTML to debug_card.html for manual inspection.")
        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print(f"Saved: {DEBUG_FILE}\n")
        print("Open it, search for a job title you saw on the page,")
        print("and find the parent <div> — note its class name.")
        return

    # Save card HTML
    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        f.write(card.prettify())
    print(f" Card HTML saved to: {DEBUG_FILE}\n")

    # Print all class names
    all_classes = set()
    for tag in card.find_all(True):
        for c in tag.get("class", []):
            all_classes.add(c)
    print(" All class names inside this card:")
    for c in sorted(all_classes):
        print(f"    .{c}")

    # Print all tag text
    print("\nAll text content (tag → text):")
    for tag in card.find_all(True):
        t = tag.get_text(strip=True)
        if t and len(t) > 2 and tag.name not in ["html", "body"]:
            classes = " ".join(tag.get("class", []))
            print(f"    <{tag.name} class='{classes}'> → {t[:120]}")

    print("\n Use the class names above to update parse_card() in this script.")
    print("Then run:  python phase1_internshala_scraper.py")


# Card Parser 

def parse_card(card, role_slug: str) -> dict | None:
    """
    Extract one job record from a card div.
    Each field tries multiple selector fallbacks.
    If fields are still empty after running --debug, update these selectors
    with the actual class names printed by debug mode.
    """
    try:
        record = {}

        # Title 
        record["title"] = first_text(
            card.find("h3", class_="job-internship-name"),
            card.find("h3", class_=re.compile(r"job|title|name", re.I)),
            card.find("a",  class_=re.compile(r"job|title", re.I)),
            card.find("h3"),
            card.find("h2"),
        )

        # Company 
        record["company"] = first_text(
            card.find("p",    class_="company-name"),
            card.find("p",    class_=re.compile(r"company", re.I)),
            card.find("a",    class_=re.compile(r"company", re.I)),
            card.find("span", class_=re.compile(r"company", re.I)),
        )

        #  Location 
        loc_container = (
            card.find("p",    class_=re.compile(r"location", re.I)) or
            card.find("div",  class_=re.compile(r"location", re.I)) or
            card.find("span", class_=re.compile(r"location", re.I)) or
            card.find("div",  class_=re.compile(r"city|cities|place", re.I))
        )
        if loc_container:
            city_links = loc_container.find_all("a")
            record["location"] = (
                ", ".join(a.get_text(strip=True) for a in city_links)
                if city_links
                else loc_container.get_text(strip=True)
            )
        else:
            
            loc_links = card.find_all("a", href=re.compile(r"/jobs/in-|/internships/in-"))
            record["location"] = ", ".join(a.get_text(strip=True) for a in loc_links)

        # Stipend / Salary
        record["stipend"] = first_text(
            card.find("span", class_="desktop"),
            card.find("span", class_="stipend"),
            )

        # Date Posted 
        
        date_tag = (
            card.find("div", class_="status-success") or
            card.find("div", class_="status-inactive")
            )
        record["date_posted"] = (
            parse_relative_date(date_tag.get_text(strip=True))
            if date_tag
            else datetime.today().strftime("%Y-%m-%d")
        )

        #  Skills
       
        skill_tags = card.find_all("div", class_="job_skill")
        record["skills"] = ", ".join(
            s.get_text(strip=True) for s in skill_tags if s.get_text(strip=True)
)

        #Job Type 
        record["job_type"] = first_text(
            card.find("span", class_=re.compile(r"job.?type|work.?type|employment", re.I)),
            card.find("div",  class_=re.compile(r"job.?type|work.?type", re.I)),
        ) or "Job"

        record["search_role"] = role_slug
        record["source"] = "internshala"

        return record if record["title"] else None

    except Exception as e:
        print(f" Card parse error: {e}")
        return None


#  Page Scraper 

def scrape_page(role_slug: str, page: int) -> list[dict]:
    url = f"https://internshala.com/jobs/{role_slug}-jobs/page-{page}/"
    print(f"  GET {url}")
    soup = get_soup(url)
    if not soup:
        return []

    cards = (
        soup.find_all("div", class_="individual_internship") or
        soup.find_all("div", class_=re.compile(r"job.?card|internship.?card", re.I)) or
        soup.find_all("div", attrs={"data-internship_id": True}) or
        soup.find_all("div", attrs={"data-job_id": True})
    )

    if not cards:
        print(f" No cards found on page {page}.")
        return []

    results = [r for card in cards if (r := parse_card(card, role_slug))]
    print(f"    → {len(results)} listings parsed")
    return results


# Main 

def run_scraper():
    all_records = []

    for role in SEARCH_ROLES:
        print(f"\n🔍 Role: {role}")
        role_count = 0
        for page in range(1, MAX_PAGES + 1):
            records = scrape_page(role, page)
            if not records:
                break
            all_records.extend(records)
            role_count += len(records)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        print(f"  Total: {role_count}")

    df = pd.DataFrame(all_records)
    before = len(df)
    df.drop_duplicates(subset=["title", "company", "date_posted"], inplace=True)
    print(f"\n🧹 Deduplicated: {before} → {len(df)} records")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved: {OUTPUT_FILE}")


# Entry Point
if __name__ == "__main__":
    print("=" * 60)
    print("  Internshala Scraper — Phase 1 (Fixed)")
    print("=" * 60)
    if DEBUG_MODE:
        run_debug()
    else:
        run_scraper()
