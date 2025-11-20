import logging
import requests
from datetime import date, datetime
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
from typing import List, Optional

from llm.mcp_servers.job_search.models import Job
from llm.mcp_servers.job_search.services.abstract_job_scraper import AbstractJobScraper

class LinkedInJobScraper(AbstractJobScraper):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def build_search_url(self, job_title: str, location: str = "", job_type: str = "", 
                    experience_level: str = "", remote: bool = False) -> str:
        """Build LinkedIn job search URL with parameters
    
        Args:
            job_title: Job title or search keywords
            location: Job location
            job_type: Job type - F (full-time), P (part-time), C (contract), etc.
            experience_level: Experience level - 1 (internship), 2 (entry), 3 (associate), etc.
            remote: Whether to filter for remote jobs
        """
        if not job_title:
            raise ValueError("job_title cannot be empty")        
        # Validate job_type if provided
        valid_job_types = ['F', 'P', 'C', 'T', 'I', 'V', 'O']
        if job_type and job_type not in valid_job_types:
            raise ValueError(f"Invalid job_type: {job_type}")
        base_url = "https://www.linkedin.com/jobs/search/"
        
        params = {
            'keywords': job_title,
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
    
    def scrape_job_listings(self, search_url: str, forbidden_titles: List[str], max_pages: int = 3) -> List[Job]:
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
                    job = self.parse_job_card(card, forbidden_titles)
                    if job:
                        jobs.append(job)
                
                # Be respectful with requests - use randomized delay
                time.sleep(random.uniform(2, 5))
                
        except requests.RequestException as e:
            logging.error(f"Error fetching job listings: {e}", exc_info=True)
         
        return jobs

    def parse_job_card(self, card, forbidden_titles) -> Optional[Job]:
        """Parse individual job card to extract job information"""
        # Create a dictionary to collect all fields first
        job_data = {}
        try:
            # Extract job title and link
            title_element = card.find('h3', class_='base-search-card__title')
            job_data['title'] = title_element.text.strip() if title_element else "N/A"
    
            # Extract company name
            company_element = card.find('h4', class_='base-search-card__subtitle')
            if not company_element:
                company_element = card.find('a', {'data-tracking-control-name': 'public_jobs_topcard-org-name'})
            job_data['company'] = company_element.text.strip() if company_element else "N/A"

            # Extract location
            location_element = card.find('span', class_='job-search-card__location')
            job_data['location'] = location_element.text.strip() if location_element else "N/A"
            
            # Add description before creating the Job object
            job_data['description'] = "Click link to view full description"
            
            # Log the collected data before creating Job object
            logging.debug(f"Attempting to create Job with data: {job_data}")
            
            # Create the Job object with all required fields
            job = Job(**job_data)
            
            # Add optional fields after creation
            link_element = card.find('a', class_='base-card__full-link')
            job.link = link_element['href'] if link_element and 'href' in link_element.attrs else "N/A"

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
                
            job = self.validate_job(job_data, forbidden_titles)
            return job
            
        except Exception as e:
            logging.error(f"Error parsing job card: {e}", exc_info=True)
            logging.error(f"Job data collected so far: {job_data}")
            return None
    
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
            return "Description not available"        
    
    def run_scraper(self, job_title, location, remote, forbidden_titles, max_pages):
        search_url = self.build_search_url(
            job_title=job_title,
            location=location,
            remote=remote
        )
    
        logging.debug(f"Search URL: {search_url}")
        
        return self.scrape_job_listings(search_url=search_url, forbidden_titles=forbidden_titles, max_pages=max_pages)