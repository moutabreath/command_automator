import asyncio
import json
from typing import List
from llm.mcp_servers.job_search.utils.time_parser import parse_time_expression
from playwright.async_api import async_playwright
import random
import logging
from urllib.parse import urlencode
from datetime import datetime

from llm.mcp_servers.job_search.models import ScrapedJob
from llm.mcp_servers.job_search.services.abstract_job_scraper import AbstractJobScraper

from utils.file_utils import GLASSDOOR_SELECTORS_FILE


class GlassdoorJobsScraper(AbstractJobScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.glassdoor.com"
        self.headers['Upgrade-Insecure-Requests'] = 'keep-alive'
        
        # Load selectors configuration
        config_path = GLASSDOOR_SELECTORS_FILE
        try:
            with open(config_path, 'r') as f:
                self.selectors = json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load selectors configuration: {e}") from e
    
    async def run_scraper(self, job_title: str, location: str, forbidden_titles: list[str], 
                          max_pages: int, max_jobs_per_page: int) -> List[ScrapedJob]:
        try:
            await self._setup_browser()
            jobs = await self._scrape_jobs(
                job_title=job_title,
                location=location, 
                forbidden_titles=forbidden_titles,
                max_pages=max_pages,
                max_jobs_per_page=max_jobs_per_page
            )
                
            # Print summary
            logging.info(f"Total jobs found: {len(jobs)}")

            return jobs
        finally:
            await self._cleanup()
        
    async def _setup_browser(self):
        """Initialize browser with stealth settings"""
        if hasattr(self, 'browser'):
            await self._cleanup()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.headers['User-Agent'],
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers=self.headers
        )
        
        self.page = await self.context.new_page()
        
        # Add stealth scripts
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

    async def _scrape_jobs(self, job_title: str, location: str, forbidden_titles: list[str],
                          max_pages: int, max_jobs_per_page: int) -> List[ScrapedJob] :
        """Main scraping method"""
        logging.info(f"Starting scrape for '{job_title}' jobs in '{location}'")        
        jobs = []
        for page_num in range(1, max_pages + 1):
            logging.info(f"=== Scraping Page {page_num} ===")
            
            url = self._build_search_url(job_title, location, page_num)
            page_jobs = await self._scrape_job_page(url, forbidden_titles, max_jobs_per_page)
            jobs.extend(page_jobs)
            
            if len(page_jobs) == 0:
                logging.info("No jobs found on this page, stopping...")
                break
            
            # Longer delay between pages
            await self._random_delay(5, 10)
        
        logging.info("=== Scraping Complete ===")
        logging.info(f"Total jobs scraped: {len(jobs)}")        
        return jobs    

    async def _random_delay(self, min_delay=2, max_delay=5):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def _cleanup(self):
        """Clean up browser resources"""
        try:
            if hasattr(self, 'context'):
                await self.context.close()
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            logging.error(f"Cleanup error: {e}", exc_info=True)
    
    def _build_search_url(self, job_title: str, location: str, page):    
        """Build Glassdoor job search URL"""
        # Calculate URL path indices based on input lengths
        location_start = 0
        location_end = len(location)
        keyword_start = location_end + 1  # +1 for the hyphen separator
        keyword_end = keyword_start + len(job_title.replace(' ', '-'))

        params = {
            'locId': 119,
            'locT': 'N',
            'sc.keyword': job_title
        }
        url_job_title = job_title.replace(' ', '-')
        path_component = f"SRCH_IL.{location_start},{location_end}_IN119_KO{keyword_start},{keyword_end}"
        return f"{self.base_url}/Job/{location}-{url_job_title}-jobs-{path_component}.htm?{urlencode(params)}"
         
    async def _handle_popups(self):
        """Handle common Glassdoor popups"""
        try:
            for _, selector in self.selectors['popups'].items():
                popup_elem = self.page.locator(selector)
                if await popup_elem.count() > 0:
                    await popup_elem.first.click()
                    await self._random_delay(1, 2)
                    
        except Exception as e:
            logging.error(f"Popup handling error: {e}", exc_info=True)
    
    async def _extract_job_details(self, job_element, forbidden_titles: list[str]) -> ScrapedJob | None:
        """Extract details from a single job listing"""
        try:
            job_data = {}
            
            # Extract each field according to configuration
            for field, config in self.selectors['job_details'].items():
                elem = job_element.locator(config['selector'])
                
                if await elem.count() > 0:
                    if config['attribute'] == 'exists':
                        job_data[field] = True
                    elif config['attribute'] == 'href':
                        await self._extract_link(job_data, field, elem)
                    elif config['attribute'] == 'src':
                        job_data[field] = await elem.get_attribute('src') or "N/A"
                    else:
                        job_data[field] = await elem.inner_text()
                else:
                    job_data[field] = False if config['attribute'] == 'exists' else "N/A"

            return self.validate_job(job_data, forbidden_titles)
        
        except Exception as e:
            logging.error(f"Error extracting job details: {e}", exc_info=True)
            return None
 
    async def _extract_link(self, job_data, field, elem):
        href = await elem.get_attribute('href')
        if href:
            job_data[field] = href if href and href.startswith('http') else f"{self.base_url}{href}"
        else:
            job_data[field] = None

    async def _scrape_job_page(self, url: str, forbidden_titles: list[str], max_jobs: int) -> List[ScrapedJob]:
        """Scrape jobs from a single page"""        
        jobs = []
        try:
            logging.debug(f"Scraping: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self._random_delay(3, 5)
            
            # Handle popups
            await self._handle_popups()
            
            # Wait for job container to load
            job_container_selectors = self.selectors['containers']['job_container']
            for job_container_selector in job_container_selectors:
                try:
                    await self.page.wait_for_selector(job_container_selector, timeout=15000)
                    break
                except Exception:
                    logging.debug(f"Container selector '{job_container_selector}' not found, trying next...")
                    continue
            else:
                logging.warning("No job container selectors matched, page structure may have changed")                
            # Get all job listings on the page
            job_elements = self.page.locator(self.selectors['containers']['job_card'])
            job_count = await job_elements.count()
            
            logging.debug(f"Found {job_count} job listings on this page")
            
            for i in range(min(job_count, max_jobs)):
                try:
                    job_element = job_elements.nth(i)
                    job = await self._extract_job_details(job_element, forbidden_titles)
                    
                    if job and job.title != "N/A":
                        jobs.append(job)
                        logging.info(f"Scraped: {job.title} at {job.company}")
                    
                    # Small delay between job extractions
                    await self._random_delay(0.5, 1.5)
                    
                except Exception as e:
                    logging.error(f"Error processing job {i}: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error scraping page {url}: {e}", exc_info=True)
        finally:
            return jobs
    
 
    def validate_job(self, job_data, forbidden_titles):
        """Validate job data against forbidden titles"""
        required_fields = ['title', 'company', 'location']
        for field in required_fields:
            if field not in job_data or not isinstance(job_data[field], str):
                logging.debug(f"Job missing required field '{field}' or invalid type: {job_data}")
                return None  # Invalid job data
        
        title_text = job_data['title']

        if any(ft.lower() in title_text.lower() for ft in (forbidden_titles or [])):
            return None

        # Prepare fields for Job construction and handle posted_date parsing
        posted_date_value = None if 'posted_date' not in job_data else job_data['posted_date']
        parsed_date = None if isinstance(posted_date_value, str) and posted_date_value.startswith("couldn't extract") else self._calc_date_from_range(posted_date_value)
        
        try:
            return ScrapedJob(
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                description= None if not('descritpion' in job_data) else self._normalize_description(job_data['descritpion']),
                link=None if not('url' in job_data) else job_data['url'] ,
                posted_date=parsed_date
            )
        except Exception as e:
            logging.error(f"Error creating Job object: {e}", exc_info=True)
            return None
        
    def _normalize_description(self, description_value):
        """Normalize description value, returning None for empty/invalid values."""
        if description_value in (None, False, "N/A", ""):
            return None
        return description_value
    

    def _calc_date_from_range(self, posted_date_str: str) -> datetime | None:
        """
        Convert a relative time string (e.g., '30d+', '1h') to a datetime object
        representing when the job was posted.
        """
        if not posted_date_str:
            return None
        
        try:
            return parse_time_expression(posted_date_str)
        except ValueError as e:
            logging.warning(f"Could not parse date string '{posted_date_str}': {e}")
            return None
 