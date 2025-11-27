#!/usr/bin/env python3
"""
Generate README.md from deals.json, filtering out expired deals.
Only shows active, current certification opportunities.
"""

import json
from datetime import datetime
import os

def load_deals():
    """Load deals from JSON file."""
    with open('data/deals.json', 'r') as f:
        return json.load(f)

def is_active(deal):
    """Check if a deal is currently active."""
    # Ongoing deals are always active
    if deal.get('ongoing', False):
        return True
    
    # Check end date for time-limited deals
    if 'end_date' in deal:
        end_date = datetime.strptime(deal['end_date'], '%Y-%m-%d')
        return datetime.now() < end_date
    
    return True

def format_deal(deal):
    """Format a single deal as markdown."""
    md = f"### {deal['provider']} - {deal['title']}\n\n"
    
    # Status line
    if deal.get('ongoing'):
        md += "**Status:** ✅ **ACTIVE** (Ongoing)\n\n"
    elif 'end_date' in deal:
        end_date = datetime.strptime(deal['end_date'], '%Y-%m-%d').strftime('%B %d, %Y')
        if 'start_date' in deal:
            start_date = datetime.strptime(deal['start_date'], '%Y-%m-%d').strftime('%B %d, %Y')
            md += f"**Status:** ✅ **ACTIVE** ({start_date} - {end_date})\n\n"
        else:
            md += f"**Status:** ✅ **ACTIVE** (Ending {end_date})\n\n"
    
    # Details
    if 'eligibility' in deal:
        md += f"**Eligibility:** {deal['eligibility']}\n\n"
    
    if 'discount' in deal:
        md += f"**Discount:** {deal['discount']}\n"
    
    if deal.get('free_retake'):
        md += "**Bonus:** Free retake if you don't pass\n"
    
    md += "\n"
    
    # Certifications
    if 'certifications' in deal:
        md += "**Available Certifications:**\n"
        for cert in deal['certifications']:
            md += f"- ✅ {cert}\n"
        md += "\n"
    
    if 'certification' in deal:
        md += f"**Certification:** {deal['certification']}\n"
        if 'exam_code' in deal:
            md += f"**Exam Code:** {deal['exam_code']}\n"
        md += "\n"
    
    # Programs (for Microsoft Partner)
    if 'programs' in deal:
        md += "**Programs:**\n"
        for prog in deal['programs']:
            md += f"- **{prog['name']}**: {prog['benefit']} ({prog['eligibility']})\n"
        md += "\n"
    
    # Includes (for ISC2)
    if 'includes' in deal:
        md += "**What's Included:**\n"
        for item in deal['includes']:
            md += f"- ✅ {item}\n"
        md += "\n"
    
    # How to claim
    if 'how_to_claim' in deal:
        md += "**How to Claim:**\n"
        for i, step in enumerate(deal['how_to_claim'], 1):
            md += f"{i}. {step}\n"
        md += "\n"
    
    # Value
    if 'value' in deal:
        md += f"**Value:** {deal['value']}\n\n"
    
    # Links
    if 'links' in deal:
        md += "**Links:**\n"
        for key, url in deal['links'].items():
            label = key.replace('_', ' ').title()
            md += f"- [{label}]({url})\n"
        md += "\n"
    
    md += "---\n\n"
    return md

def generate_readme(data):
    """Generate complete README content."""
    today = datetime.now().strftime('%B %d, %Y')
    
    md = """# 🎓 Latest IT Certification Deals, Free Exams & Beta Programs

> **Auto-updated:** Daily via GitHub Actions

A curated list of **free IT certification exam vouchers**, **beta exam opportunities**, and **discount codes** from major cloud providers and IT certification vendors.

---

## 🚀 Quick Links

- [Active Free Voucher Programs](#-active-free-voucher-programs)
- [Beta Exam Opportunities](#-beta-exam-opportunities)
- [How to Get Notified](#-how-to-get-notified)

---

## 🎯 Active Free Voucher Programs

"""
    
    # Filter and add active deals
    active_deals = [deal for deal in data['deals'] if is_active(deal)]
    
    if not active_deals:
        md += "*No active deals at this time. Check back soon!*\n\n"
    else:
        for deal in active_deals:
            md += format_deal(deal)
    
    # Beta exam section
    md += """## 🧪 Beta Exam Opportunities

Beta exams are **heavily discounted or free** in exchange for feedback. Check these sources weekly:

"""
    
    for source in data.get('beta_sources', []):
        md += f"### {source['provider']} Beta Exams\n\n"
        md += f"**Typical Discount:** {source['discount']}\n\n"
        md += "**How to Find:**\n"
        for url in source['sources']:
            md += f"- {url}\n"
        md += "\n---\n\n"
    
    # Footer
    md += """## 📅 How to Get Notified

This repository is **automatically updated daily** via GitHub Actions!

### Automated Tracking

- ✅ **Every day at 9 AM UTC** - Script checks for new deals
- ✅ **Watch this repo** - Get notified of updates

### Manual Tracking Methods

**Follow on LinkedIn:**
- [Microsoft Learn](https://www.linkedin.com/showcase/microsoft-learn/)
- [AWS Training & Certification](https://www.linkedin.com/showcase/aws-training-and-certification/)

**Subscribe to Newsletters:**
- [Microsoft Born to Learn](https://borntolearn.mslearn.net/)
- AWS Training emails

**Join Communities:**
- [r/certifications](https://reddit.com/r/certifications) subreddit
- IT certification Discord servers

---

## 🤝 Contributing

Found a new deal? Please contribute!

1. Fork this repository
2. Update `data/deals.json` with the new deal
3. Submit a pull request

---

## ⚠️ Disclaimers

- **Verify Details:** Always check official sources before registering
- **Terms & Conditions:** Read program T&Cs carefully
- **Expiration Dates:** Voucher dates can change without notice
- **Eligibility:** Some programs have geographic or demographic restrictions
- **Automated Updates:** GitHub Actions runs daily but may have delays

---

**⭐ Star this repo** to bookmark and get notified of updates!

---

Made with ❤️ for the IT certification community | Auto-updated via GitHub Actions 🤖
"""
    
    return md

def main():
    """Main function."""
    print("🔄 Generating README from active deals...")
    
    # Load deals
    data = load_deals()
    
    # Filter active deals
    active_count = sum(1 for deal in data['deals'] if is_active(deal))
    print(f"✅ Found {active_count} active deals (filtered out {len(data['deals']) - active_count} expired)")
    
    # Generate README
    readme_content = generate_readme(data)
    
    # Write to file
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ README.md generated successfully!")

if __name__ == "__main__":
    main()
