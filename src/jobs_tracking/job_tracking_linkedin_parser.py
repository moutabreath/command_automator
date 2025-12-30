import logging
import requests
from bs4 import BeautifulSoup

def extract_linkedin_job(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    company_name = "N/A"
    job_title = "N/A"
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Extract Job Title 
        # Strategy: Find the <p> that contains the phrase "Developer" or "Engineer"
        # and grab only the 'Direct' text (NavigableString) to avoid nested SVG/Link text.
        # We look for all <p> tags and check their direct strings
        for p in soup.find_all('p'):
            # .find(text=True, recursive=False) gets text that isn't inside nested tags
            direct_text = p.find(text=True, recursive=False)
            if direct_text and len(direct_text.strip()) > 3:
                # Often the title is the longest direct string in a header area
                job_title = direct_text.strip()
                break 

        # 2. Extract Company Name
        # Strategy: Look for the <a> tag that leads to a company page
        company_tag = soup.find('a', href=lambda x: x and '/company/' in x)
        # We use the same 'direct text' trick to avoid spans/icons inside the link
        if company_tag:
            company_name = company_tag.find(text=True, recursive=False) or company_tag.get_text()
        return {
            "job_title": job_title,
            "company_name": company_name.strip()
        }

    except Exception as e:
           logging.exception(f"error scraping linkedin page {e}")
           return {
            "job_title": job_title,
            "company_name": company_name.strip()
        }