import asyncio, logging, requests, time, random

from datetime import date, datetime
from typing import List, Optional

from bs4 import BeautifulSoup
import urllib.parse

from llm.mcp_servers.job_search.models import ScrapedJob
from llm.mcp_servers.job_search.services.job_scrapers.abstract_jobs_scraper_service import AbstractJobsScraperService

class LinkedInJobsScraperService(AbstractJobsScraperService):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    async def run_scraper(self, job_title: str, location: str = "", remote: bool = False, 
                    forbidden_titles: List[str] = None, max_pages: int = 3,
                    job_type: str = "", experience_level: str = "") -> List[ScrapedJob]:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.run_scraper_sync(job_title, location, remote, forbidden_titles, max_pages, job_type, experience_level)
    )

       
    def run_scraper_sync(self, job_title: str, location: str = "", remote: bool = False, 
                    forbidden_titles: List[str] = None, max_pages: int = 3,
                    job_type: str = "", experience_level: str = "") -> List[ScrapedJob]:
        """Run the LinkedIn job scraper with specified parameters
        
        Args:
            job_title: Job title or search keywords
            location: Job location
            remote: Whether to filter for remote jobs
            forbidden_titles: List of job titles to exclude
            max_pages: Maximum number of pages to scrape
            job_type: Job type filter (F, P, C, etc.)
            experience_level: Experience level filter (1, 2, 3, etc.)
            
        Returns:
            List of Job objects
        """
        if not (job_title) or job_title == "" or not(location) or location == "":
            logging.error("Job title and location must be provided.")
            return []

        if not(forbidden_titles):
            forbidden_titles = []
        
        search_url = self._build_search_url(
            job_title=job_title,
            location=location,
            remote=remote
        )
    
        logging.debug(f"Search URL: {search_url}")
        
        return self._scrape_job_listings(search_url=search_url, forbidden_titles=forbidden_titles, max_pages=max_pages)
        
    def _build_search_url(self, job_title: str, location: str = "", job_type: str = "", 
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
    
    def _scrape_job_listings(self, search_url: str, forbidden_titles: List[str], max_pages: int = 3) -> List[ScrapedJob]:
        """Scrape job listings from LinkedIn search results"""
        jobs = []
        
        for page in range(max_pages):            
            
            # Add page parameter to URL
            page_url = search_url + f"&start={page * 25}"

            logging.info(f"Scraping page {page_url}..")
            soup = None
            try:                
                response = self.session.get(page_url, timeout=30)
                response.raise_for_status()                
                soup = BeautifulSoup(response.content, 'lxml')                      
            except requests.RequestException as e:
                logging.exception(f"Error fetching job listings: {e}")
                return jobs
            
            # Find job cards
            job_cards = soup.find_all('div', class_='base-card')
            
            if not job_cards:
                logging.warning("No job cards found on this page")
                break
            
            for card in job_cards:
                job = self._parse_job_card(card, forbidden_titles)
                if job:
                    jobs.append(job)
            
            # Be respectful with requests - use randomized delay
            time.sleep(random.uniform(2, 5))          
         
        return jobs

    def _validate_job(self, job_data: dict) -> bool:
        """Validate job data to filter out invalid entries"""
        title = job_data.get('title', '')
        company = job_data.get('company', '')
        link = job_data.get('link', '')
        
        # Filter out jobs where title, company, or link only contains '*' characters
        if (title.strip('*').strip() == '' or company.strip('*').strip() == '' or link.strip('*').strip() == ''):
            return False
        return True

    def _parse_job_card(self, card, forbidden_titles) -> Optional[ScrapedJob]:
        """Parse individual job card to extract job information"""
              
        # Create a dictionary to collect all fields first
        job_data = {}
        try:
            # Extract job title and link
            title_element = card.find('h3', class_='base-search-card__title')
            job_data['title'] = title_element.text.strip() if title_element else "N/A"
            if any(forbidden_title.lower() in  job_data['title'].lower() for forbidden_title in (forbidden_titles or [])):
                logging.info(f"Skipping forbidden job title: {job_data['title']}")
                return None
    
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
                        
            # Add optional fields after creation
            link_element = card.find('a', class_='base-card__full-link')
            job_data['job_url'] = link_element['href'] if link_element and 'href' in link_element.attrs else "N/A"
 

            # Extract posted date
            date_element = card.find('time', class_='job-search-card__listdate')
            posted_date_str = None
            if date_element and date_element.has_attr('datetime'):
                posted_date_str = date_element['datetime']
            
            try:
               job_data['posted_date'] = datetime.fromisoformat(posted_date_str).date() if posted_date_str else date.today()
          
            except (ValueError, TypeError):
                logging.warning(f"Could not parse date '{posted_date_str}'. Using today's date.")
                job_data['posted_date'] = date.today()

            logging.debug(f"Attempting to create Job with data: {job_data}")
            
            # Validate job data before creating Job object
            if not self._validate_job(job_data):
                logging.info(f"Skipping invalid job: {job_data['title']}")
                return None
                
            job = ScrapedJob(**job_data)
            return job
            
        except Exception as e:
            logging.exception(f"Error parsing job card: {e}. Job data collected so far: {job_data}")
            return None
    
    def _get_job_description(self, job_url: str) -> str:
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
