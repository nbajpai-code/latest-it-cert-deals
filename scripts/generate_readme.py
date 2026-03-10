#!/usr/bin/env python3
"""
generate_readme.py
------------------
Generates README.md from data/deals.json.

Key behaviours:
  - Expired deals (end_date in the past, ongoing=false) are EXCLUDED
  - Ongoing deals are always shown
  - Providers sorted alphabetically within each section
"""

import json
import os
from datetime import datetime

REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
DEALS_FILE = os.path.join(REPO_ROOT, 'data', 'deals.json')
README_FILE = os.path.join(REPO_ROOT, 'README.md')


def load_deals():
    with open(DEALS_FILE) as f:
        return json.load(f)


def is_active(deal):
    """Return True if the deal is currently active / not expired."""
    if deal.get('status') != 'active':
        return False
    if deal.get('ongoing', False):
        return True
    end_date_str = deal.get('end_date')
    if not end_date_str:
        return True  # No end date → assume still active
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        return end_date >= datetime.now().date()
    except ValueError:
        return True  # Malformed date → don't hide it


def format_deal_section(deal):
    """Render a single deal as a README markdown section."""
    provider = deal.get('provider', 'Unknown')
    title    = deal.get('title', '')
    value    = deal.get('value', '')
    links    = deal.get('links', {})
    main_url = links.get('main', '#')

    # Status / expiry line
    if deal.get('ongoing'):
        status_line = 'Status: ✅ ACTIVE (Ongoing)'
    else:
        end_date = deal.get('end_date', 'TBD')
        status_line = f'Status: ✅ ACTIVE (Expires: {end_date})'

    # Eligibility / certifications
    eligibility = deal.get('eligibility', '')
    certifications = deal.get('certifications', [])
    if not certifications and deal.get('certification'):
        certifications = [deal['certification']]

    # Programs (e.g. Microsoft partner)
    programs = deal.get('programs', [])

    # How to claim
    steps = deal.get('how_to_claim', [])

    # Includes list (e.g. ISC2)
    includes = deal.get('includes', [])

    lines = [f'### {provider} — {title}', status_line]

    if eligibility:
        lines.append(f'**Eligibility:** {eligibility}')

    if certifications:
        lines.append('**Available Certifications:**')
        for c in certifications:
            lines.append(f'- ✅ {c}')

    if programs:
        lines.append('**Programs:**')
        for p in programs:
            lines.append(f"- **{p['name']}:** {p['benefit']} _{p.get('eligibility', '')}_")

    if includes:
        lines.append('**What\'s Included:**')
        for i in includes:
            lines.append(f'- ✅ {i}')

    if steps:
        lines.append('**How to Claim:**')
        for i, step in enumerate(steps, 1):
            lines.append(f'{i}. {step}')

    lines.append(f'**Value:** {value}')

    # Links
    link_parts = []
    for key, url in links.items():
        label = key.capitalize()
        link_parts.append(f'[{label}]({url})')
    if link_parts:
        lines.append('**Links:** ' + ' · '.join(link_parts))

    return '\n'.join(lines)


def format_beta_sources(beta_sources):
    sections = []
    for b in sorted(beta_sources, key=lambda x: x.get('provider', '')):
        provider = b.get('provider', '')
        discount = b.get('discount', '')
        sources  = b.get('sources', [])
        lines = [
            f'### {provider} Beta Exams',
            f'**Typical Discount:** {discount}',
            '**How to Find:**',
        ]
        for s in sources:
            lines.append(f'- [{s}]({s})')
        sections.append('\n'.join(lines))
    return '\n\n'.join(sections)


def generate_readme(data):
    today = datetime.now().strftime('%Y-%m-%d')

    all_deals  = data.get('deals', [])
    active_deals = [d for d in all_deals if is_active(d)]
    expired_count = len(all_deals) - len(active_deals)

    beta_sources = data.get('beta_sources', [])

    # Sort active deals: ongoing first, then by provider name
    active_deals.sort(key=lambda d: (not d.get('ongoing', False), d.get('provider', '')))

    deal_sections = '\n\n'.join(format_deal_section(d) for d in active_deals)
    beta_section  = format_beta_sources(beta_sources)

    expired_note = ''
    if expired_count > 0:
        expired_note = f'\n> ℹ️ {expired_count} deal(s) have expired and are hidden. Update `data/deals.json` to remove them.\n'

    return f"""# 🎓 Latest IT Certification Deals, Free Exams & Beta Programs

> **Auto-updated:** Daily via GitHub Actions  
> **Last check:** {today}{expired_note}

A curated list of **free** IT certification exam vouchers, beta exam opportunities,
and discount codes from major cloud providers and IT certification vendors.

---

## 🚀 Quick Links

- [Active Free Voucher Programs](#-active-free-voucher-programs)
- [Beta Exam Opportunities](#-beta-exam-opportunities)
- [How to Get Notified](#-how-to-get-notified)
- [Daily Deal Tracker](cert-deals-update.md)

---

## 🎯 Active Free Voucher Programs

_{len(active_deals)} active program(s) as of {today}_

{deal_sections}

---

## 🧪 Beta Exam Opportunities

Beta exams are heavily discounted or free in exchange for feedback.
Check these sources **weekly** — spots fill up fast:

{beta_section}

---

## 📅 How to Get Notified

### Automated Tracking
- ✅ Every day at 9 AM UTC — script checks all major vendor feeds
- ✅ [Watch / Star this repo](https://github.com/nbajpai-code/latest-it-cert-deals/subscription) to receive update notifications
- ✅ RSS feed updates committed daily to [`cert-deals-update.md`](cert-deals-update.md)

### Manual Tracking Methods

**Follow on LinkedIn:**
- [Microsoft Learn](https://www.linkedin.com/showcase/microsoft-learn/)
- [AWS Training & Certification](https://www.linkedin.com/showcase/aws-training-and-certification/)
- [Google Cloud](https://www.linkedin.com/showcase/google-cloud/)

**Subscribe to Newsletters / Blogs:**
- [Microsoft Born to Learn](https://borntolearn.mslearn.net/)
- [AWS Training & Certification Blog](https://aws.amazon.com/blogs/training-and-certification/)
- [Linux Foundation Newsletter](https://www.linuxfoundation.org/newsletter/)

**Join Communities:**
- [r/certifications](https://reddit.com/r/certifications) subreddit
- [r/AWSCertifications](https://reddit.com/r/AWSCertifications)
- IT certification Discord servers

---

## 🤝 Contributing

Found a new deal? Please contribute!

1. Fork this repository
2. Add the deal to [`data/deals.json`](data/deals.json) following the existing schema
3. Submit a pull request

**Schema example:**
```json
{{
  "id": "vendor-program-year",
  "provider": "VendorName",
  "title": "Program Title",
  "status": "active",
  "ongoing": false,
  "end_date": "YYYY-MM-DD",
  "eligibility": "Who can claim this",
  "certifications": ["Cert Name (CODE-001)"],
  "value": "$X saved",
  "how_to_claim": ["Step 1", "Step 2"],
  "links": {{ "main": "https://..." }}
}}
```

---

## ⚠️ Disclaimers

- **Verify Details:** Always check official sources before registering
- **Terms & Conditions:** Read program T&Cs carefully
- **Expiration Dates:** Voucher dates can change without notice
- **Eligibility:** Some programs have geographic or demographic restrictions
- **Automated Updates:** GitHub Actions runs daily but may have delays

---

⭐ **Star this repo** to bookmark and get notified of updates!  
Made with ❤️ for the IT certification community | Auto-updated via GitHub Actions 🤖
"""


def main():
    data = load_deals()
    readme = generate_readme(data)
    with open(README_FILE, 'w') as f:
        f.write(readme)
    print(f'✅ README.md generated successfully.')
    print(f'   Active deals: {len([d for d in data.get("deals", []) if is_active(d)])}')


if __name__ == '__main__':
    main()
