#!/usr/bin/env python3
"""
Draft Application Emails
-------------------------
Reads jobs.csv (produced by scraper.py) and, for every NEW job that has
a direct contact email in its listing, generates a personalized draft
application email as a .txt file in drafts/ for you to review and send
yourself.

Jobs that don't expose a contact email (e.g. Upwork, which requires
applying through its own proposal system) are instead logged to
apply_via_platform.csv with a direct link, so nothing falls through
the cracks.

Nothing is ever sent automatically — every email is a draft for you
to look over first.
"""

import csv
import json
import os
import re

PROFILE_PATH = "my_profile.json"
JOBS_CSV = "jobs.csv"
DRAFTED_LOG = "drafted_seen.json"
DRAFTS_DIR = "drafts"
PLATFORM_APPLY_CSV = "apply_via_platform.csv"

EMAIL_TEMPLATE = """Subject: Flutter Developer for {title}

Hi{company_greeting},

{pitch}

I saw your listing for "{title}" and it's a strong match for what I do —
I'd love to help you build this out.

{portfolio_line}{rate_line}
Happy to share more details or hop on a quick call whenever works for you.

Best,
{name}
{contact_email}
"""


def load_profile():
    if not os.path.exists(PROFILE_PATH):
        raise SystemExit(
            f"Missing {PROFILE_PATH}. Copy the template and fill in your details first."
        )
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_drafted():
    if os.path.exists(DRAFTED_LOG):
        with open(DRAFTED_LOG, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_drafted(drafted_set):
    with open(DRAFTED_LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(drafted_set), f, indent=2)


def safe_filename(text, max_len=60):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len] or "job"


def ensure_platform_csv():
    if not os.path.exists(PLATFORM_APPLY_CSV):
        with open(PLATFORM_APPLY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date_found", "source", "title", "company", "url"])


def main():
    profile = load_profile()
    if profile.get("name") == "YOUR NAME HERE":
        raise SystemExit(
            f"Please fill in your real details in {PROFILE_PATH} before running this."
        )

    if not os.path.exists(JOBS_CSV):
        raise SystemExit(f"{JOBS_CSV} not found — run scraper.py first.")

    os.makedirs(DRAFTS_DIR, exist_ok=True)
    ensure_platform_csv()

    drafted = load_drafted()
    new_drafts = 0
    new_platform_rows = 0

    with open(JOBS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    platform_rows_to_add = []

    for row in rows:
        url = row.get("url", "").strip()
        if not url or url in drafted:
            continue

        contact_email = row.get("contact_email", "").strip()
        title = row.get("title", "Flutter Developer Role").strip()
        company = row.get("company", "").strip()

        if contact_email:
            portfolio_line = (
                f"Portfolio: {profile['portfolio_url']}\n" if profile.get("portfolio_url") else ""
            )
            rate_line = (
                f"My typical rate is {profile['rate']}.\n" if profile.get("rate") else ""
            )
            email_body = EMAIL_TEMPLATE.format(
                title=title,
                company_greeting=f" {company} team" if company else "",
                pitch=profile.get("pitch", ""),
                portfolio_line=portfolio_line,
                rate_line=rate_line,
                name=profile.get("name", ""),
                contact_email=profile.get("contact_email", ""),
            )

            filename = f"{safe_filename(company + '-' + title)}.txt"
            path = os.path.join(DRAFTS_DIR, filename)
            with open(path, "w", encoding="utf-8") as out:
                out.write(f"TO: {contact_email}\n")
                out.write(f"JOB LINK: {url}\n\n")
                out.write(email_body)

            new_drafts += 1
        else:
            platform_rows_to_add.append([
                row.get("date_found", ""), row.get("source", ""), title, company, url
            ])
            new_platform_rows += 1

        drafted.add(url)

    if platform_rows_to_add:
        with open(PLATFORM_APPLY_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(platform_rows_to_add)

    save_drafted(drafted)

    print(f"Drafted {new_drafts} email(s) in {DRAFTS_DIR}/")
    print(f"Logged {new_platform_rows} platform-only job(s) to {PLATFORM_APPLY_CSV}")


if __name__ == "__main__":
    main()
