"""
Markdown mirror generator for Global Caribbeans.
Reads the HTML file, strips chrome, and writes a clean index.md
that AI tools can fetch and read without noise.

Run: py scripts/generate_markdown_mirrors.py
"""

import re
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md

SITE_ROOT = Path(__file__).parent.parent
HTML_FILE = SITE_ROOT / "Global Caribbeans HTML File.html"
OUTPUT_FILE = SITE_ROOT / "index.md"
LLMS_FILE = SITE_ROOT / "llms.txt"

CANONICAL_URL = "https://globalcaribbeans.com/"
TODAY = date.today().isoformat()

# Tags to strip entirely (presentational / executable only)
STRIP_TAGS = ["script", "style", "noscript", "iframe", "svg"]

# Exact class names on decorative-only elements to remove
STRIP_EXACT_CLASSES = {
    "hero-bubble", "hero-glow", "hero-glow-1", "hero-glow-2",
    "hero-particles", "hero-wave", "hero-bubbles", "footer-wave",
    "footer-bubbles", "share-toast", "live-dot", "divider-line",
    "back-to-top-btn",
}

# Class fragments on structural chrome to remove
STRIP_CLASS_FRAGMENTS = ["filter-wrap", "filter-card", "jobs-grid", "results-bar", "section-divider"]


def should_strip(tag):
    if not hasattr(tag, 'attrs') or tag.attrs is None:
        return False
    classes = set(tag.get("class", []))
    if classes & STRIP_EXACT_CLASSES:
        return True
    class_str = " ".join(classes).lower()
    return any(frag in class_str for frag in STRIP_CLASS_FRAGMENTS)


def clean_markdown(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*\d{2}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[|]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'!\[\]\([^)]*\)', '', text)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_mirror():
    print(f"Reading: {HTML_FILE.name}")
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Extract metadata
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Global Caribbeans"

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    # Remove executable/presentational tags
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove decorative and structural chrome by class
    for tag in list(soup.find_all(True)):
        if should_strip(tag):
            tag.decompose()

    # Remove footer (not meaningful for AI — contact info is in llms.txt)
    for tag in soup.find_all("footer"):
        tag.decompose()

    # Remove interactive form elements
    for tag in soup.find_all(["button", "input", "select", "label"]):
        tag.decompose()

    # Drop empty div/span wrappers
    changed = True
    while changed:
        changed = False
        for tag in soup.find_all(["div", "span"]):
            if not tag.get_text(strip=True):
                tag.decompose()
                changed = True

    # Get body content
    body = soup.find("body")
    body_html = str(body) if body else str(soup)

    # Convert to markdown
    raw_md = md(body_html, heading_style="ATX", bullets="-")
    cleaned = clean_markdown(raw_md)

    # Since the jobs grid is dynamic (loaded from Supabase at runtime),
    # append a static note so AI understands what the page contains.
    static_supplement = """
## Job Categories

Remote roles are listed across 13 categories:
- Customer Support
- Software Development
- Sales
- Online Marketing
- Accounting/Bookkeeping
- Admin
- Operations
- Project Management
- Data/Analytics
- IT/Engineering
- Recruiting
- Legal
- Other

## About the Job Listings

Close to 2,000 remote jobs are added within any given 30-day period. Listings auto-expire after 30 days. The board updates every 5 minutes. Jobs are sourced from companies hiring Worldwide, across the Americas, and in Latin America/Caribbean. Each listing includes an average salary benchmark drawn from Careevo's proprietary title intelligence database.

## Career Services

Caribbean professionals who want help positioning themselves for the remote job market can access career services through Careevo at https://careevo.co/authority/?utm_source=globalcaribbeans. Services start at JMD 15,500 (approx. USD 108) and include career alignment, resume revamp, LinkedIn optimization, and introduction audio scripts.
"""

    # Build frontmatter
    frontmatter = f"""---
title: {title}
description: {description}
url: {CANONICAL_URL}
last_updated: {TODAY}
---

"""

    mirror_content = frontmatter + cleaned + static_supplement
    OUTPUT_FILE.write_text(mirror_content, encoding="utf-8")
    print(f"Written: {OUTPUT_FILE.name}")
    print(f"Size: {len(mirror_content)} characters")
    print()
    print("Summary: 1 page processed -> index.md generated")
    print(f"Mirror URL: {CANONICAL_URL}index.md")


if __name__ == "__main__":
    generate_mirror()
