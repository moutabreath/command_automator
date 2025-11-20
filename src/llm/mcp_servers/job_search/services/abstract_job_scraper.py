from datetime import datetime
import logging

from llm.mcp_servers.job_search.models import Job
from llm.mcp_servers.services.shared_service import SharedService

from .time_parser import parse_time_expression

class AbstractJobScraper(SharedService):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def validate_job(self, job_data, forbidden_titles):
        """Validate job data against forbidden titles"""
        required_keys = ['title', 'company', 'location', 'description', 'url', 'posted_date']
        if not all(key in job_data for key in required_keys):
            logging.warning(f"Missing required keys in job_data: {set(required_keys) - set(job_data.keys())}")
            return None
        if any(title.lower() in job_data['title'].lower() for title in forbidden_titles):
            return None
        return Job(
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data['description'],
                    link=job_data['url'],
                    posted_date=self._calc_date_from_range(job_data['posted_date'])
                )
    
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