import logging
from typing import List, Tuple

from llm.mcp_servers.job_search.models import ScrapedJob
from llm.mcp_servers.services.company_mcp_service import CompanyReadService
from llm.mcp_servers.services.models import UserApplicationResponseCode


class JobsFilterService:
    """Handles filtering of scraped jobs against applied jobs"""
    
    def __init__(self, compan_read_service: CompanyReadService):
        self.company_mcp_service = compan_read_service
    
    async def filter_jobs(self, scraped_jobs: List[ScrapedJob], user_id: str) -> Tuple[List, List]:
        """Filter jobs that have already been applied for"""

        if (len(scraped_jobs) == 0):
            logging.info("No jobs to filter")
            return [], []

        response = await self.company_mcp_service.get_all_user_applications(user_id)
        if response.code != UserApplicationResponseCode.SUCCESS:
            logging.error(f"Failed to get user applications for user_id {user_id}: {response.error_message}")
            return scraped_jobs, []
        
        tracked_companies_with_positions = response.user_applications
        if len(tracked_companies_with_positions) == 0:
            return scraped_jobs, []
        
        company_lookup = {
            app.company_name.strip().lower(): app 
            for app in tracked_companies_with_positions
        }

        applied_company_names = [app.company_name.strip().lower() for app in tracked_companies_with_positions]
        
        filtered_jobs = []
        tracked_jobs = []
        logging.info(f"iterating scraped_jobs of size: {len(scraped_jobs)}")

        for scraped_job in scraped_jobs:
            scraped_company_name = scraped_job.company.strip().lower()
            if scraped_company_name not in applied_company_names:
                filtered_jobs.append(scraped_job)
                continue

            company_data = company_lookup.get(scraped_company_name)
            if not company_data:
                filtered_jobs.append(scraped_job)
                continue
        
            applied_jobs = company_data.tracked_job
            scraped_company_applied_job_urls = [job.job_url for job in applied_jobs]
            scraped_company_applied_job_titles = [job.job_title.strip().lower() for job in applied_jobs]

            if scraped_job.link in scraped_company_applied_job_urls or scraped_job.title.strip().lower() in scraped_company_applied_job_titles:
                tracked_jobs.append(scraped_job)
            else:
                filtered_jobs.append(scraped_job)
                
        return filtered_jobs, tracked_jobs
