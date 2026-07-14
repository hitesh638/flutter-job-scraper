# Flutter Freelance Job Scraper (100% Free)

Pulls Flutter / mobile-app freelance & remote job listings from free,
public sources and appends new matches to `jobs.csv`. Runs automatically
several times a day via GitHub Actions — no server, no paid API, no
LinkedIn scraping (which violates LinkedIn's Terms of Service and isn't
supported here).

## Sources used
- [RemoteOK](https://remoteok.com) — free public JSON API
- [WeWorkRemotely](https://weworkremotely.com) — free public RSS feed
- [Arbeitnow](https://www.arbeitnow.com) — free public JSON API
- [Jobicy](https://jobicy.com) — free public JSON API (pre-filtered by "flutter" tag)
- [Upwork RSS search](https://www.upwork.com) — free public RSS search feed for "flutter"

## Setup (5 minutes, all free)

1. **Fill in `my_profile.json`** with your real name, a 1-2 line pitch,
   portfolio link, rate (optional), and contact email. This is what
   gets used to personalize your draft application emails.
2. **Create a new GitHub repo** (public repos get unlimited free Actions
   minutes; private repos get 2,000 free minutes/month, plenty for this).
3. Upload all files, keeping the folder structure:
   ```
   scraper.py
   draft_applications.py
   my_profile.json
   requirements.txt
   jobs.csv
   seen_jobs.json
   drafted_seen.json
   apply_via_platform.csv
   drafts/
   .github/workflows/scrape.yml
   README.md
   ```
4. Go to the **Actions** tab of your repo and enable workflows if prompted.
5. That's it. The workflow runs automatically every 4 hours (6x/day).
   You can also trigger it manually anytime: **Actions → Flutter Job
   Scraper → Run workflow**.
6. Each run does two things:
   - Appends new matching jobs to `jobs.csv`
   - For any new job that lists a **direct contact email**, drafts a
     personalized application in `drafts/` as a `.txt` file — just
     open it, review, copy into your email client, and hit send
   - For jobs with **no direct email** (e.g. Upwork, which requires
     applying through its own system), the job + link get logged to
     `apply_via_platform.csv` instead, so you know to apply manually there

### Nothing is ever auto-sent
Every email in `drafts/` is a **draft only**. You review and send each
one yourself — this keeps quality high and avoids your email getting
flagged as spam for mass-sending generic messages, and it matches how
freelance clients actually respond best: personalized, human-reviewed
pitches over blind automated ones.

## Customizing

- **Change how often it runs**: edit the `cron` line in
  `.github/workflows/scrape.yml`. E.g. `"0 */2 * * *"` = every 2 hours
  (12x/day), `"0 6,12,18 * * *"` = 3x/day at 6am/12pm/6pm UTC.
- **Change keywords**: edit the `KEYWORDS` list at the top of
  `scraper.py` (e.g. add `"react native"`, `"ios developer"`, etc.).
- **Add more sources**: add a new `fetch_xyz()` function following the
  same pattern as the existing ones, and add it to the list in `main()`.

## Running locally (optional, to test before pushing)

```bash
pip install -r requirements.txt
python scraper.py
```

This will fetch fresh listings and append any new ones to `jobs.csv`
right on your machine.

## Why not LinkedIn?

LinkedIn's Terms of Service explicitly prohibit scraping, and they
actively detect and block it (and have pursued legal action against
scrapers, e.g. *hiQ Labs v. LinkedIn*). This tool intentionally sticks
to sources that offer free, public, scraping-friendly access instead.
