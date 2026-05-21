"""
Fetches active job listings from Supabase and writes jobs.md —
a clean, AI-readable markdown file of current listings on Global Caribbeans.

Run locally: py scripts/generate_jobs_md.py
Also run by GitHub Actions every 6 hours automatically.
"""

import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

SUPABASE_URL = 'https://zgnpwkzjkuulqsyolmdg.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpnbnB3a3pqa3V1bHFzeW9sbWRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxMDAwODQsImV4cCI6MjA5MDY3NjA4NH0.UjLl9JFqnKwA7XCPvTzOPA1S6pxge3xu86M34FpBE4g'

OUTPUT = Path(__file__).parent.parent / 'jobs.md'
TODAY = datetime.now(timezone.utc).strftime('%Y-%m-%d')
NOW = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}


def fetch_jobs():
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    cols = 'id,slug,title,company,primary_category,salary_display,location_display,bilingual,posted_at,job_link'
    PAGE_SIZE = 1000
    all_rows = []
    offset = 0

    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/jobs"
            f"?select={cols}"
            f"&is_active=eq.true"
            f"&is_visible=eq.true"
            f"&posted_at=gte.{thirty_days_ago}"
            f"&order=posted_at.desc"
            f"&limit={PAGE_SIZE}"
            f"&offset={offset}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        page = resp.json()
        if not isinstance(page, list) or len(page) == 0:
            break
        all_rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return all_rows


def build_markdown(jobs):
    lines = [
        '---',
        'title: Global Caribbeans — Current Remote Job Listings',
        'description: Live remote job listings curated for Caribbean professionals. Sourced from the Global Caribbeans job board and updated every 6 hours.',
        'url: https://globalcaribbeans.com/',
        f'last_updated: {NOW}',
        '---',
        '',
        '# Current Remote Job Listings — Global Caribbeans',
        '',
        f'**{len(jobs)} active remote jobs** as of {TODAY}.',
        'All listings are curated for Caribbean professionals and sourced from companies hiring Worldwide, across the Americas, and in Latin America/Caribbean.',
        'Listings auto-expire after 30 days. This file is regenerated every 6 hours.',
        '',
        '---',
        '',
    ]

    # Group by category
    categories = {}
    for job in jobs:
        cat = (job.get('primary_category') or 'Other').strip()
        categories.setdefault(cat, []).append(job)

    for cat in sorted(categories.keys()):
        cat_jobs = categories[cat]
        lines.append(f'## {cat} ({len(cat_jobs)} open roles)')
        lines.append('')
        for job in cat_jobs:
            title = (job.get('title') or '').strip()
            company = (job.get('company') or '').strip()
            salary = (job.get('salary_display') or 'Not Disclosed').strip()
            location = (job.get('location_display') or '').strip()
            bilingual = job.get('bilingual', False)
            slug = (job.get('slug') or job.get('id') or '').strip()
            posted = (job.get('posted_at') or '')[:10]
            gc_url = f'https://globalcaribbeans.com/#card-{slug}' if slug else 'https://globalcaribbeans.com'

            lines.append(f'### {title}')
            lines.append(f'- **Company:** {company}')
            lines.append(f'- **Salary:** {salary}')
            lines.append(f'- **Location:** {location}')
            if bilingual:
                lines.append('- **Bilingual:** English/Spanish required')
            lines.append(f'- **Posted:** {posted}')
            lines.append(f'- **View Job:** {gc_url}')
            lines.append('')

    return '\n'.join(lines)


if __name__ == '__main__':
    print('Fetching jobs from Supabase...')
    jobs = fetch_jobs()
    print(f'Fetched {len(jobs)} active jobs')

    content = build_markdown(jobs)
    OUTPUT.write_text(content, encoding='utf-8')

    print(f'Written: {OUTPUT.name}')
    print(f'Size: {len(content):,} characters')
    print(f'Mirror URL: https://raw.githubusercontent.com/Careevo/global-caribbeans-ai/main/jobs.md')
