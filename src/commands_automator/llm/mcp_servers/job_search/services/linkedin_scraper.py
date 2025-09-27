import logging
import requests
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import time
import urllib.parse
from typing import List, Optional
from commands_automator.llm.mcp_servers.job_search.models import Job
from commands_automator.llm.mcp_servers.services.shared_service import SharedService

class LinkedInJobScraper(SharedService):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
    
    def build_search_url(self, keywords: str, location: str = "", job_type: str = "", 
                    experience_level: str = "", remote: bool = False) -> str:
        """Build LinkedIn job search URL with parameters
    
        Args:
            keywords: Search keywords
            location: Job location
            job_type: Job type - F (full-time), P (part-time), C (contract), etc.
            experience_level: Experience level - 1 (internship), 2 (entry), 3 (associate), etc.
            remote: Whether to filter for remote jobs
        """
        if not keywords:
            raise ValueError("Keywords cannot be empty")
        
        # Validate job_type if provided
        valid_job_types = ['F', 'P', 'C', 'T', 'I', 'V', 'O']
        if job_type and job_type not in valid_job_types:
            raise ValueError(f"Invalid job_type: {job_type}")
        base_url = "https://www.linkedin.com/jobs/search/"
        
        params = {
            'keywords': keywords,
            'location': location,
            'trk': 'public_jobs_jobs-search-bar_search-submit',
            'position': '1',
            'pageNum': '0'
        }
        
        # Add optional filters
        if job_type:
            params['f_JT'] = job_type  # F (full-time), P (part-time), C (contract), etc.
        
        if experience_level:
            params['f_E'] = experience_level  # 1 (internship), 2 (entry), 3 (associate), etc.
        
        if remote:
            params['f_WT'] = '2'  # Remote work filter
        
        return base_url + "?" + urllib.parse.urlencode(params)
    
    def scrape_job_listings(self, search_url: str, max_pages: int = 3) -> List[Job]:
        """Scrape job listings from LinkedIn search results"""
        jobs = []
        
        try:
            for page in range(max_pages):
                logging.info(f"Scraping page {page + 1}...")
                
                # Add page parameter to URL
                page_url = search_url + f"&start={page * 25}"
                
                response = self.session.get(page_url, timeout=30)
                response.raise_for_status()                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Find job cards
                job_cards = soup.find_all('div', class_='base-card')
                
                if not job_cards:
                    logging.warning("No job cards found on this page")
                    break
                
                for card in job_cards:
                    job = self.parse_job_card(card)
                    if job:
                        jobs.append(job)
                
                # Be respectful with requests - use randomized delay
                import random
                time.sleep(random.uniform(2, 5))
                
        except requests.RequestException as e:
            logging.error(f"Error fetching job listings: {e}", exc_info=True)
         
        return jobs    

    def parse_job_card(self, card) -> Optional[Job]:
        """Parse individual job card to extract job information"""
        job = Job()
        try:
            # Extract job title and link
            title_element = card.find('h3', class_='base-search-card__title')
            job.title = title_element.text.strip() if title_element else "N/A"

            link_element = card.find('a', class_='base-card__full-link')
            job.link = link_element['href'] if link_element and 'href' in link_element.attrs else "N/A"
       
            # Extract company name
            company_element = card.find('h4', class_='base-search-card__subtitle')
            if not company_element:
                company_element = card.find('a', {'data-tracking-control-name': 'public_jobs_topcard-org-name'})
            company = company_element.text.strip() if company_element else "N/A"
            job.company = company
            
            # Extract location
            location_element = card.find('span', class_='job-search-card__location')
            job.location = location_element.text.strip() if location_element else "N/A"
            
            # Extract posted date
            date_element = card.find('time', class_='job-search-card__listdate')
            posted_date_str = None
            if date_element and date_element.has_attr('datetime'):
                posted_date_str = date_element['datetime']
            
            try:
                job.posted_date = datetime.fromisoformat(posted_date_str).date() if posted_date_str else date.today()
            except (ValueError, TypeError):
                logging.warning(f"Could not parse date '{posted_date_str}'. Using today's date.")
                job.posted_date = date.today()
            
            # For description, we'd need to visit the individual job page
            # For now, we'll leave it as a placeholder
            job.description = "Click link to view full description"
            
        except (AttributeError, KeyError) as e:
            logging.error(f"Error parsing job card attributes: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error parsing job card: {e}", exc_info=True)
        finally:
            return job
    
    def get_job_description(self, job_url: str) -> str:
        """Get detailed job description from individual job page"""
        try:
            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Look for job description
            desc_element = soup.find('div', class_='show-more-less-html__markup')
            if desc_element:
                return desc_element.get_text(separator=' ', strip=True)
            
            return "Description not available"
            
        except Exception as e:
            logging.error(f"Error fetching job description: {e}", exc_info=True)
            return "Error fetching description"
    
