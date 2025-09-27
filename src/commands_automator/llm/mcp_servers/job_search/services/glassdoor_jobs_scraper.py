import asyncio
import json
from datetime import datetime
import os
from playwright.async_api import async_playwright
import random
import logging
from urllib.parse import urlencode
from pathlib import Path
from .time_parser import parse_time_expression

from commands_automator.llm.mcp_servers.job_search.models import Job
from commands_automator.llm.mcp_servers.services.shared_service import SharedService

class GlassdoorJobsScraper(SharedService):
    def __init__(self):
        self.base_url = "https://www.glassdoor.com"
        self.jobs = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Load selectors configuration
        config_path = Path(__file__).parent.parent / "config" / "glassdoor_selectors.json"
        try:
            with open(config_path, 'r') as f:
                self.selectors = json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load selectors configuration: {e}")
    
    async def setup_browser(self):
        """Initialize browser with stealth settings"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
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

    async def random_delay(self, min_delay=2, max_delay=5):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def cleanup(self):
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
    
    def build_search_url(self, job_title, location, page=1):
        """Build Glassdoor job search URL"""
        params = {
            'locId': 119,
            'locT': 'N',
            'sc.keyword' : job_title
        }
        # Example URL: https://www.glassdoor.com/Job/israel-senior-software-engineer-jobs-SRCH_IL.0,6_IN119_KO7,31.htm?sc.keyword=senior+software+engineer
        url_job_title = job_title.replace(' ', '-')
        return f"{self.base_url}/Job/{location}-{url_job_title}-jobs-SRCH_IL.0,6_IN119_KO7,31.htm?{urlencode(params)}"
      
    async def handle_popups(self):
        """Handle common Glassdoor popups"""
        try:
            for popup_name, selector in self.selectors['popups'].items():
                popup_elem = self.page.locator(selector)
                if await popup_elem.count() > 0:
                    await popup_elem.first.click()
                    await self.random_delay(1, 2)
                
        except Exception as e:
            logging.error(f"Popup handling error: {e}", exc_info=True)
    
    async def extract_job_details(self, job_element):
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
                        href = await elem.get_attribute('href')
                        job_data[field] = href if href and href.startswith('http') else f"{self.base_url}{href}"
                    elif config['attribute'] == 'src':
                        job_data[field] = await elem.get_attribute('src') or "N/A"
                    else:
                        job_data[field] = await elem.inner_text()
                else:
                    job_data[field] = False if config['attribute'] == 'exists' else "N/A"

            return Job(
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                description=job_data['description'],
                link=job_data['url'],
                posted_date=self.calc_date_from_range(job_data['posted_date'])
            )
            
        except Exception as e:
            logging.error(f"Error extracting job details: {e}", exc_info=True)
            return Job() 

            
  
    def calc_date_from_range(self, posted_date_str: str) -> datetime:
        """
        Convert a relative time string (e.g., '30d+', '1h') to a datetime object
        representing when the job was posted.
        """
        if not posted_date_str:
            return datetime.now()  # Default to current time if no date string provided
            
        try:
            return parse_time_expression(posted_date_str)
        except ValueError as e:
            logging.warning(f"Could not parse date string '{posted_date_str}': {e}")
            return datetime.now()  # Default to current time if parsing fails
            
    def filter_israel_center(self):
        """Filter jobs for Israel center region"""
        center_keywords = ['tel aviv', 'herzliya', 'petah tikva', 'ramat gan', 'givatayim', 
                          'bnei brak', 'holon', 'bat yam', 'center', 'central']
        
        filtered_jobs = []
        for job in self.jobs:
            location = job.location.lower()
            if any(keyword in location for keyword in center_keywords):
                filtered_jobs.append(job)
        
        logging.info(f"Filtered to {len(filtered_jobs)} jobs in Israel center region")
        return filtered_jobs


    async def scrape_job_page(self, url, max_jobs=50):
        """Scrape jobs from a single page"""
        try:
            logging.debug(f"Scraping: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(3, 5)
            
            # Handle popups
            await self.handle_popups()
            
            # Wait for job container to load
            job_container_selectors = self.selectors['containers']['job_container']
            for job_container_selector in job_container_selectors:
                try:
                    await self.page.wait_for_selector(job_container_selector, timeout=15000)
                    break
                except:
                    continue
            
            # Get all job listings on the page
            job_elements = self.page.locator(self.selectors['containers']['job_card'])
            job_count = await job_elements.count()
            
            logging.debug(f"Found {job_count} job listings on this page")
            
            jobs_scraped = 0
            for i in range(min(job_count, max_jobs)):
                try:
                    job_element = job_elements.nth(i)
                    job = await self.extract_job_details(job_element)
                    
                    if job and job.title != "N/A":
                        self.jobs.append(job)
                        jobs_scraped += 1
                        logging.info(f"Scraped: {job.title} at {job.company}")
                    
                    # Small delay between job extractions
                    await self.random_delay(0.5, 1.5)
                    
                except Exception as e:
                    logging.error(f"Error processing job {i}: {e}")
                    continue
            
            return jobs_scraped
            
        except Exception as e:
            logging.error(f"Error scraping page {url}: {e}", exc_info=True)
            return 0
    
    async def scrape_jobs(self, job_title, location, max_pages=5, max_jobs_per_page=30):
        """Main scraping method"""
        logging.info(f"Starting scrape for '{job_title}' jobs in '{location}'")        
        
        try:
            total_jobs = 0
            
            for page in range(1, max_pages + 1):
                logging.info(f"=== Scraping Page {page} ===")
                
                url = self.build_search_url(job_title, location, page)
                jobs_on_page = await self.scrape_job_page(url, max_jobs_per_page)
                total_jobs += jobs_on_page
                
                if jobs_on_page == 0:
                    logging.info("No jobs found on this page, stopping...")
                    break
                
                # Longer delay between pages
                await self.random_delay(5, 10)
            
            logging.info("=== Scraping Complete ===")
            logging.info(f"Total jobs scraped: {total_jobs}")
            
        except Exception as e:
            logging.error(f"Error during scraping: {e}", exc_info=True)
        
        finally:
            await self.cleanup()
    
 
    async def run_scraper(self, job_title, location, max_pages=3, max_jobs_per_page=20):
        
        await self.setup_browser()
        # Scrape software engineer jobs in Israe,l
        await self.scrape_jobs(
            job_title=job_title,
            location=location, 
            max_pages=max_pages,
            max_jobs_per_page=max_jobs_per_page
        )
        
        # Filter for center region
        center_jobs = self.filter_israel_center()
            
        # Print summary
        logging.info(f"Total jobs found: {len(self.jobs)}")
        logging.info(f"Total filtered jobs: {len(center_jobs)}")

        return center_jobs
  

    