#!/usr/bin/env python3
"""
daily_cert_deals.py
-------------------
Scrapes RSS/blog feeds from major IT certification vendors and produces
a daily Markdown report saved to cert-deals-update.md.

Sources:
  - Microsoft Learn / Born to Learn (TechCommunity RSS)
  - AWS Training & Certification Blog RSS
  - CompTIA News RSS
  - Google Cloud Blog RSS
  - Cisco Learning Network Blog RSS
  - Linux Foundation Blog RSS
  - (ISC)² Blog RSS
"""

import requests
import os
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

# ---------------------------------------------------------------------------
# Keywords that indicate a deal / discount / free exam announcement
# ---------------------------------------------------------------------------
DEAL_KEYWORDS = [
    'exam', 'certification', 'beta', 'free', 'discount', 'voucher',
    'retake', 'launch', 'new cert', 'available now', 'announced',
    'associate', 'practitioner', 'challenge', 'offer', 'promo',
    'no cost', 'waived', 'complimentary', 'earn', 'badge', 'coupon',
]

LOOKBACK_DAYS = 7


def fetch_rss(url, timeout=15):
    """Fetch raw bytes from an RSS feed URL. Returns None on failure."""
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (compatible; CertDealsBot/1.0; '
            '+https://github.com/nbajpai-code/latest-it-cert-deals)'
        )
    }
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"  ⚠️  Error fetching {url}: {e}")
        return None


def parse_rss_feed(url, source_label):
    """
    Generic RSS parser.  Looks for <item> elements, checks publication
    date (within LOOKBACK_DAYS) and keyword relevance.
    Returns a list of deal dicts.
    """
    content = fetch_rss(url)
    if not content:
        return []

    try:
        soup = BeautifulSoup(content, 'xml')
    except Exception:
        soup = BeautifulSoup(content, 'html.parser')

    items = soup.find_all('item')
    deals = []
    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    for item in items:
        title_tag = item.find('title')
        link_tag  = item.find('link')
        date_tag  = item.find('pubDate') or item.find('published') or item.find('dc:date')
        desc_tag  = item.find('description') or item.find('summary')

        title       = title_tag.get_text(strip=True)  if title_tag else ''
        link        = link_tag.get_text(strip=True)   if link_tag  else ''
        description = desc_tag.get_text(strip=True)   if desc_tag  else ''
        date_str    = date_tag.get_text(strip=True)   if date_tag  else ''

        # --- Parse the date ---
        pub_date = None
        for fmt in (
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
        ):
            try:
                pub_date = datetime.strptime(date_str[:len(fmt) + 4].strip(), fmt)
                # Strip tzinfo for naive comparison
                pub_date = pub_date.replace(tzinfo=None)
                break
            except (ValueError, TypeError):
                continue

        if pub_date is None:
            # If we can't parse the date, include if keywords match — better
            # than silently dropping potentially relevant content
            pass
        elif pub_date < cutoff:
            continue

        # --- Keyword check ---
        haystack = (title + ' ' + description).lower()
        if any(kw in haystack for kw in DEAL_KEYWORDS):
            deals.append({
                'source': source_label,
                'title':  title,
                'link':   link,
                'date':   pub_date.strftime('%Y-%m-%d') if pub_date else 'Unknown',
            })

    return deals


# ---------------------------------------------------------------------------
# Per-provider parsers
# ---------------------------------------------------------------------------

def parse_microsoft_learn():
    """Microsoft TechCommunity — community-wide blog RSS (most reliable endpoint)."""
    print("  🔍 Microsoft Learn...")
    # The plugin-based per-blog URLs no longer work. Use the community-wide RSS
    # and filter for learn/cert related posts by keyword (handled by parse_rss_feed).
    feeds = [
        'https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/Community?interaction.style=blog',
        'https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=MicrosoftLearnBlog',
    ]
    deals = []
    for url in feeds:
        result = parse_rss_feed(url, 'Microsoft Learn')
        deals.extend(result)
        if result:
            break  # Stop on first successful feed
        time.sleep(1)
    print(f"     → {len(deals)} item(s) found")
    return deals


def parse_aws_training():
    """AWS Training & Certification blog RSS."""
    print("  🔍 AWS Training & Certification...")
    deals = parse_rss_feed(
        'https://aws.amazon.com/blogs/training-and-certification/feed/',
        'AWS Training'
    )
    print(f"     → {len(deals)} item(s) found")
    return deals


def parse_google_cloud():
    """Google Cloud blog — filter for certification/skills posts."""
    print("  🔍 Google Cloud Blog...")
    deals = parse_rss_feed(
        'https://cloudblog.withgoogle.com/rss/',
        'Google Cloud'
    )
    # Extra filter: Google's blog covers many topics; narrow further
    cert_kw = ['certification', 'skill badge', 'cloud digital leader',
                'professional cert', 'associate cert', 'voucher', 'free exam']
    deals = [d for d in deals if any(k in d['title'].lower() for k in cert_kw)]
    print(f"     → {len(deals)} item(s) found")
    return deals


def parse_cisco_learning():
    """Cisco Learning Network — DevNet blog RSS."""
    print("  🔍 Cisco Learning Network...")
    # Cisco's main learning-network search RSS is unreliable; use the DevNet blog
    deals = parse_rss_feed(
        'https://blogs.cisco.com/developer/feed',
        'Cisco Learning'
    )
    print(f"     → {len(deals)} item(s) found")
    return deals


def parse_linux_foundation():
    """Linux Foundation blog — tries multiple known RSS paths."""
    print("  🔍 Linux Foundation...")
    urls = [
        'https://linuxfoundation.org/blog/rss',
        'https://www.linuxfoundation.org/feed/',
        'https://www.linuxfoundation.org/blog/feed',
    ]
    for url in urls:
        deals = parse_rss_feed(url, 'Linux Foundation')
        if deals:
            print(f"     → {len(deals)} item(s) found")
            return deals
        time.sleep(0.5)
    print("     → 0 item(s) found (feed unavailable)")
    return []


def parse_isc2():
    """(ISC)² blog — tries multiple known feed paths."""
    print("  🔍 (ISC)² Blog...")
    urls = [
        'http://feeds.feedburner.com/isc2/blog',
        'https://blog.isc2.org/isc2_blog/atom.xml',
        'https://www.isc2.org/Blog/rss',
    ]
    for url in urls:
        deals = parse_rss_feed(url, '(ISC)²')
        if deals:
            print(f"     → {len(deals)} item(s) found")
            return deals
        time.sleep(0.5)
    print("     → 0 item(s) found (feed unavailable)")
    return []


def parse_comptia():
    """CompTIA blog — tries multiple known feed paths."""
    print("  🔍 CompTIA Blog...")
    urls = [
        'https://www.comptia.org/rssfeeds/comptia',
        'https://comptia.org/blog/rss',
        'https://www.comptia.org/feed',
    ]
    for url in urls:
        deals = parse_rss_feed(url, 'CompTIA')
        if deals:
            print(f"     → {len(deals)} item(s) found")
            return deals
        time.sleep(0.5)
    print("     → 0 item(s) found (feed unavailable)")
    return []


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def load_active_deals():
    """Load currently active deals from data/deals.json for the report header."""
    deals_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'deals.json')
    try:
        with open(deals_path) as f:
            data = json.load(f)
        today = datetime.now().date()
        active = []
        for d in data.get('deals', []):
            if d.get('status') != 'active':
                continue
            if d.get('ongoing'):
                active.append(d)
                continue
            end_date_str = d.get('end_date')
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    if end_date >= today:
                        active.append(d)
                except ValueError:
                    active.append(d)
        return active
    except Exception as e:
        print(f"  ⚠️  Could not load deals.json: {e}")
        return []


def generate_report(news_items):
    today = datetime.now().strftime('%Y-%m-%d')
    active_deals = load_active_deals()

    md = f"""# 📊 Daily IT Certification Deal Tracker
**Last Updated:** {today}  
**Status:** Automated check completed ✅

---

## 🎯 Currently Active Free / Discounted Programs ({len(active_deals)} active)

"""
    if active_deals:
        for d in active_deals:
            label  = f"{d.get('provider', '')} — {d.get('title', '')}"
            value  = d.get('value', '')
            links  = d.get('links', {})
            url    = links.get('main', links.get('cert', '#'))
            expiry = 'Ongoing' if d.get('ongoing') else d.get('end_date', 'Check source')
            md += f"- **[{label}]({url})** — {value} _(Expires: {expiry})_\n"
    else:
        md += "_No active deals found in deals.json at this time._\n"

    md += f"""
---

## 📰 Latest Certification News (Last {LOOKBACK_DAYS} Days)

"""
    if news_items:
        # Deduplicate by title
        seen = set()
        unique_items = []
        for item in news_items:
            key = item['title'].lower().strip()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        for item in unique_items:
            md += f"- **[{item['source']}]** [{item['title']}]({item['link']}) _({item['date']})_\n"
    else:
        md += (
            "_No new certification deal announcements detected this week. "
            "Check the quick links below for manual verification._\n"
        )

    md += """
---

## 🔗 Quick Links for Manual Checks

| Vendor | Direct Link |
|--------|-------------|
| Microsoft Learn Blog | [techcommunity.microsoft.com](https://techcommunity.microsoft.com/t5/microsoft-learn-blog/bg-p/MicrosoftLearnBlog) |
| Microsoft Beta Exams | [borntolearn.mslearn.net](https://borntolearn.mslearn.net/) |
| AWS Training & Cert | [aws.amazon.com/blogs/training-and-certification](https://aws.amazon.com/blogs/training-and-certification/) |
| AWS Beta Exams | [LinkedIn — AWS Training](https://www.linkedin.com/showcase/aws-training-and-certification/) |
| Google Cloud Certs | [cloud.google.com/certification](https://cloud.google.com/certification) |
| CompTIA Beta Exams | [comptia.org/testing/beta-exams](https://www.comptia.org/testing/beta-exams) |
| (ISC)² Programs | [isc2.org/exams](https://www.isc2.org/exams) |
| Oracle University | [education.oracle.com](https://education.oracle.com) |
| Cisco Learning Network | [learningnetwork.cisco.com](https://learningnetwork.cisco.com) |
| Linux Foundation | [training.linuxfoundation.org](https://training.linuxfoundation.org) |
| r/certifications | [reddit.com/r/certifications](https://reddit.com/r/certifications) |
"""
    return md


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('\n🔍 Scanning certification feeds...\n')

    news_items = []
    parsers = [
        parse_microsoft_learn,
        parse_aws_training,
        parse_google_cloud,
        parse_cisco_learning,
        parse_linux_foundation,
        parse_isc2,
        parse_comptia,
    ]

    for parser in parsers:
        try:
            news_items.extend(parser())
        except Exception as e:
            print(f"  ❌ Parser {parser.__name__} failed: {e}")
        time.sleep(1)  # Be polite between requests

    print(f'\n✅ Total unique items found across all sources: {len(news_items)}')

    report = generate_report(news_items)

    output_path = os.path.join(os.path.dirname(__file__), '..', 'cert-deals-update.md')
    with open(output_path, 'w') as f:
        f.write(report)
    print(f'📄 Report written to: {output_path}')

    # Write outputs for GitHub Actions
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f"update_date={datetime.now().strftime('%Y-%m-%d')}", file=fh)
            print(f"deals_found={len(news_items)}", file=fh)


if __name__ == '__main__':
    main()
