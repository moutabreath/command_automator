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

        # 1. Extract Job Title from <title> tag
        # Strategy: Find the <title> tag and parse it
        # LinkedIn format: "Company hiring Job Title in Location | LinkedIn"
        # or "Job Title - Company | Job Posting"
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Remove " | LinkedIn" suffix if present
            if " | LinkedIn" in title_text:
                title_text = title_text.split(" | LinkedIn")[0]
            
            # Try to extract job title from "Company hiring Job Title in Location" format
            if " hiring " in title_text:
                parts = title_text.split(" hiring ")
                if len(parts) > 1:
                    # Get the part after "hiring" and before "in Location"
                    job_and_location = parts[1]
                    if " in " in job_and_location:
                        job_title = job_and_location.split(" in ")[0].strip()
                    else:
                        job_title = job_and_location.strip()
            # Alternative format: "Job Title at Company"
            elif " at " in title_text:
                job_title = title_text.split(" at ")[0].strip()
            # Fallback: use the whole cleaned title
            else:
                job_title = title_text

        # 2. Extract Company Name
        # Strategy: Look for the <a> tag that leads to a company page
        company_tag = soup.find('a', href=lambda x: x and '/company/' in x)
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