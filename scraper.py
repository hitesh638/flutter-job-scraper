#!/usr/bin/env python3
"""
Flutter Freelance Job Scraper
------------------------------
Pulls Flutter / mobile-app freelance & remote job listings from FREE,
public, ToS-friendly sources (no LinkedIn — LinkedIn scraping violates
their ToS and is not supported):

  1. RemoteOK          - free public JSON API
  2. WeWorkRemotely     - free public RSS feed
  3. Arbeitnow          - free public JSON API
  4. Jobicy             - free public JSON API
  5. Upwork RSS search  - free public RSS search feed

New matches (deduped against previous runs) are appended to jobs.csv.
Designed to be run on a schedule (e.g. via GitHub Actions, several
times a day) with zero cost and zero external accounts required.
"""

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

try:
    import feedparser
except ImportError:
    feedparser = None

KEYWORDS = ["flutter", "dart mobile", "flutter developer", "flutter app"]

CSV_PATH = "jobs.csv"
SEEN_PATH = "seen_jobs.json"

CSV_HEADERS = ["date_found", "source", "title", "company", "location", "url", "tags",
               "contact_email", "description"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FlutterJobScraper/1.0; +https://github.com/)"
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Domains that are platform noise, not real contact addresses
EMAIL_DOMAIN_BLOCKLIST = ("sentry.io", "example.com", "noreply", "no-reply")


def matches_keywords(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def extract_email(text):
    """Pull the first plausible contact email out of a job description, if any."""
    if not text:
        return ""
    for match in EMAIL_RE.findall(text):
        if not any(bad in match.lower() for bad in EMAIL_DOMAIN_BLOCKLIST):
            return match
    return ""


def load_seen():
    if os.path.exists(SEEN_PATH):
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_set):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(seen_set), f, indent=2)


def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_jobs(jobs):
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for job in jobs:
            writer.writerow([job.get(h, "") for h in CSV_HEADERS])


# ---------------------------------------------------------------------
# Source fetchers - each wrapped in try/except so one failure doesn't
# break the others.
# ---------------------------------------------------------------------

def fetch_remoteok():
    results = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue  # first item is a legal notice, skip it
            title = item.get("position", "")
            tags = " ".join(item.get("tags", []))
            description = item.get("description", "") or ""
            blob = f"{title} {tags} {description}"
            if matches_keywords(blob):
                results.append({
                    "date_found": datetime.now(timezone.utc).isoformat(),
                    "source": "RemoteOK",
                    "title": title,
                    "company": item.get("company", ""),
                    "location": item.get("location", "Remote"),
                    "url": item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id')}"),
                    "tags": tags,
                    "contact_email": extract_email(description),
                    "description": description[:600],
                })
    except Exception as e:
        print(f"[RemoteOK] fetch failed: {e}", file=sys.stderr)
    return results


def fetch_weworkremotely():
    results = []
    if feedparser is None:
        print("[WeWorkRemotely] feedparser not installed, skipping", file=sys.stderr)
        return results
    try:
        feed = feedparser.parse(
            "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        )
        for entry in feed.entries:
            summary = entry.get("summary", "") or ""
            blob = f"{entry.get('title', '')} {summary}"
            if matches_keywords(blob):
                title = entry.get("title", "")
                # WWR titles are often "Company: Job Title"
                company = title.split(":")[0].strip() if ":" in title else ""
                results.append({
                    "date_found": datetime.now(timezone.utc).isoformat(),
                    "source": "WeWorkRemotely",
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "url": entry.get("link", ""),
                    "tags": "",
                    "contact_email": extract_email(summary),
                    "description": re.sub("<[^<]+?>", "", summary)[:600],
                })
    except Exception as e:
        print(f"[WeWorkRemotely] fetch failed: {e}", file=sys.stderr)
    return results


def fetch_arbeitnow():
    results = []
    try:
        resp = requests.get(
            "https://www.arbeitnow.com/api/job-board-api", headers=HEADERS, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            tags = " ".join(item.get("tags", []))
            description = item.get("description", "") or ""
            blob = f"{item.get('title', '')} {tags} {description}"
            if matches_keywords(blob):
                results.append({
                    "date_found": datetime.now(timezone.utc).isoformat(),
                    "source": "Arbeitnow",
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", "Remote") or "Remote",
                    "url": item.get("url", ""),
                    "tags": tags,
                    "contact_email": extract_email(description),
                    "description": re.sub("<[^<]+?>", "", description)[:600],
                })
    except Exception as e:
        print(f"[Arbeitnow] fetch failed: {e}", file=sys.stderr)
    return results


def fetch_jobicy():
    results = []
    try:
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"tag": "flutter"},
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("jobs", []):
            description = item.get("jobDescription", "") or ""
            # already tag-filtered by API, so no extra keyword check needed
            results.append({
                "date_found": datetime.now(timezone.utc).isoformat(),
                "source": "Jobicy",
                "title": item.get("jobTitle", ""),
                "company": item.get("companyName", ""),
                "location": item.get("jobGeo", "Remote") or "Remote",
                "url": item.get("url", ""),
                "tags": "flutter",
                "contact_email": extract_email(description),
                "description": re.sub("<[^<]+?>", "", description)[:600],
            })
    except Exception as e:
        print(f"[Jobicy] fetch failed: {e}", file=sys.stderr)
    return results


def fetch_upwork_rss():
    results = []
    if feedparser is None:
        print("[Upwork] feedparser not installed, skipping", file=sys.stderr)
        return results
    try:
        feed = feedparser.parse(
            "https://www.upwork.com/ab/feed/jobs/rss?q=flutter&sort=recency"
        )
        for entry in feed.entries:
            summary = entry.get("summary", "") or ""
            results.append({
                "date_found": datetime.now(timezone.utc).isoformat(),
                "source": "Upwork",
                "title": entry.get("title", ""),
                "company": "",
                "location": "Remote/Freelance",
                "url": entry.get("link", ""),
                "tags": "flutter",
                # Upwork never exposes a contact email — must apply via platform
                "contact_email": "",
                "description": re.sub("<[^<]+?>", "", summary)[:600],
            })
    except Exception as e:
        print(f"[Upwork] fetch failed: {e}", file=sys.stderr)
    return results


def main():
    ensure_csv()
    seen = load_seen()

    all_jobs = []
    for fetcher in (fetch_remoteok, fetch_weworkremotely, fetch_arbeitnow,
                     fetch_jobicy, fetch_upwork_rss):
        all_jobs.extend(fetcher())

    new_jobs = []
    for job in all_jobs:
        url = job.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        new_jobs.append(job)

    if new_jobs:
        append_jobs(new_jobs)
        save_seen(seen)
        print(f"Added {len(new_jobs)} new job(s) to {CSV_PATH}")
    else:
        print("No new matching jobs found this run.")


if __name__ == "__main__":
    main()
