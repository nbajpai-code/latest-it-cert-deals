import requests
import re
from datetime import datetime
import os

def get_deals():
    url = "https://raw.githubusercontent.com/mRs-/Black-Friday-Deals/master/README.md"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching deals: {e}")
        return None

def parse_deals(content):
    deals = []
    # Simple regex to find links and text in list items
    # Looking for format: - [Title](Link) - Description or similar
    # Adjusting regex to capture various formats commonly found in markdown lists
    
    lines = content.split('\n')
    current_category = "General"
    in_toc = False
    
    for line in lines:
        line = line.strip()
        
        # Check for headers as categories
        if line.startswith('##'):
            header = line.lstrip('#').strip()
            if "Table of Contents" in header:
                in_toc = True
                continue
            else:
                in_toc = False
                current_category = header
            continue
            
        # Skip if we are in TOC
        if in_toc:
            continue

        # Check for table rows
        if line.startswith('|'):
            # Skip header separator lines
            if '---' in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            # Expected format: | Emoji | [Title](Link) | Description | Discount |
            # parts will be ['', 'Emoji', '[Title](Link)', 'Description', 'Discount', '']
            
            if len(parts) >= 5:
                link_col = parts[2]
                description = parts[3]
                
                # Extract title and link from [Title](Link)
                match = re.search(r'\[(.*?)\]\((.*?)\)', link_col)
                if match:
                    title = match.group(1).strip()
                    link = match.group(2).strip()
                    
                    deals.append({
                        'category': current_category,
                        'title': title,
                        'link': link,
                        'description': description
                    })
            
    return deals

def generate_markdown(deals):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    md = f"""# 🛍️ Black Friday & Cyber Monday Deals {datetime.now().year}

> **Auto-updated hourly** from Nov 1 to Dec 15.
> Last updated: `{now}`

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/nbajpai-code/latest-it-cert-deals/graphs/commit-activity)

Here is a curated list of the best Black Friday deals for developers, macOS/iOS software, and books.

## 🏷️ Active Deals

| Category | Deal | Description | Link |
|:---|:---|:---|:---:|
"""
    
    for deal in deals:
        # Create a nice button for the link
        link_btn = f"[👉 Get Deal]({deal['link']})"
        
        # Escape pipes in description to not break table
        desc = deal['description'].replace('|', '\|')
        title = deal['title'].replace('|', '\|')
        
        md += f"| **{deal['category']}** | **{title}** | {desc} | {link_btn} |\n"
        
    md += """
---
*Deals sourced from community repositories.*
"""
    return md

def main():
    print("Fetching deals...")
    content = get_deals()
    if not content:
        print("No content found.")
        return

    print("Parsing deals...")
    deals = parse_deals(content)
    print(f"Found {len(deals)} deals.")

    print("Generating markdown...")
    md_content = generate_markdown(deals)

    output_file = "blackfriday.md"
    with open(output_file, "w") as f:
        f.write(md_content)
    
    print(f"Successfully updated {output_file}")

if __name__ == "__main__":
    main()
