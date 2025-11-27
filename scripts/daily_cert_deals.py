import requests
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

def fetch_rss(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_microsoft_learn():
    # TechCommunity RSS for Microsoft Learn Blog (Skills Hub Blog)
    # url = "https://techcommunity.microsoft.com/plugins/custom/microsoft/o365/custom-blog-rss?blogId=skills-hub-blog"
    # content = fetch_rss(url)
    # if not content:
    return []

    soup = BeautifulSoup(content, 'html.parser')
    items = soup.find_all('item')
    deals = []
    
    keywords = ['exam', 'certification', 'beta', 'free', 'discount', 'voucher', 'challenge']
    
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date_str = item.pubDate.text
        description = item.description.text if item.description else ""
        
        # Simple date parsing (RFC 822)
        # e.g., "Wed, 26 Nov 2025 12:00:00 GMT"
        try:
            pub_date = datetime.strptime(pub_date_str[:25], "%a, %d %b %Y %H:%M:%S")
        except:
            continue

        # Check if within last 7 days
        if datetime.now() - pub_date > timedelta(days=7):
            continue

        # Check keywords
        if any(k in title.lower() or k in description.lower() for k in keywords):
            deals.append({
                'source': 'Microsoft Learn',
                'title': title,
                'link': link,
                'date': pub_date.strftime("%Y-%m-%d")
            })
            
    return deals

def parse_aws_training():
    # AWS doesn't have a clean RSS for just training, using the general blog tag or similar
    # Using the 'Training and Certification' category feed if available, or parsing the blog page directly
    # For stability, let's try the official blog RSS for the category
    url = "https://aws.amazon.com/blogs/training-and-certification/feed/"
    content = fetch_rss(url)
    if not content:
        return []

    soup = BeautifulSoup(content, 'html.parser')
    items = soup.find_all('item')
    deals = []
    
    keywords = ['exam', 'certification', 'beta', 'free', 'discount', 'voucher', 'retake']
    
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date_str = item.pubDate.text
        
        try:
            # AWS format often: "Wed, 26 Nov 2025 12:00:00 +0000"
            pub_date = datetime.strptime(pub_date_str[:25], "%a, %d %b %Y %H:%M:%S")
        except:
            continue

        if datetime.now() - pub_date > timedelta(days=7):
            continue

        if any(k in title.lower() for k in keywords):
            deals.append({
                'source': 'AWS Training',
                'title': title,
                'link': link,
                'date': pub_date.strftime("%Y-%m-%d")
            })
            
    return deals

def generate_report(deals):
    today = datetime.now().strftime("%Y-%m-%d")
    
    md = f"""# 📊 Weekly IT Certification Update
**Date:** {today}
**Status:** Automated check completed

## 📰 Latest News (Last 7 Days)
"""

    if not deals:
        md += "\nNo specific 'deal' keywords found in the last 7 days. Check the links below for general updates.\n"
    else:
        for deal in deals:
            md += f"- **[{deal['source']}]** [{deal['title']}]({deal['link']}) ({deal['date']})\n"

    md += """
## 🔗 Quick Links for Manual Checks
- [Microsoft Learn Blog](https://techcommunity.microsoft.com/t5/microsoft-learn-blog/bg-p/MicrosoftLearnBlog)
- [AWS Training & Certification Blog](https://aws.amazon.com/blogs/training-and-certification/)
- [CompTIA Beta Exams](https://www.comptia.org/testing/beta-exams)
- [(ISC)² Exams](https://www.isc2.org/exams)
"""
    return md

def main():
    print("🔍 Searching for deals...")
    
    deals = []
    deals.extend(parse_microsoft_learn())
    deals.extend(parse_aws_training())
    
    print(f"Found {len(deals)} relevant items.")
    
    report = generate_report(deals)
    
    with open('cert-deals-update.md', 'w') as f:
        f.write(report)
        
    # Write to GITHUB_OUTPUT
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f"update_date={datetime.now().strftime('%Y-%m-%d')}", file=fh)
            print(f"deals_found={len(deals)}", file=fh)

if __name__ == "__main__":
    main()
