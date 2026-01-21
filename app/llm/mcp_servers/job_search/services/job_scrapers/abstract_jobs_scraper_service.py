from abc import ABC, abstractmethod
from typing import List
from llm.mcp_servers.job_search.models import ScrapedJob


class AbstractJobsScraperService(ABC):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
    @abstractmethod
    async def run_scraper(self, job_title: str, location: str, remote: bool = False, 
                   forbidden_titles: List[str] = None, max_pages: int = 3) -> List[ScrapedJob]:
        """Run the job scraper with specified parameters"""        
        pass
        