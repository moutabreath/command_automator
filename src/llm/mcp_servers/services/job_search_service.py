import logging
from typing import List, Dict, Any, Optional, Tuple

from llm.mcp_servers.job_search.services.job_scrapers.abstract_jobs_scraper_service import AbstractJobsScraperService
from llm.mcp_servers.job_search.services.job_scrapers.glassdoor_jobs_scraper_service import GlassdoorJobsScraperService
from llm.mcp_servers.job_search.services.job_scrapers.linkedin_jobs_scraper_service import LinkedInJobsScraperService
from llm.mcp_servers.job_search.services.jobs_filter_service import JobsFilterService
from llm.mcp_servers.job_search.services.jobs_saver_service import JobsSaverService
from llm.mcp_servers.services.company_mcp_service import CompanyReaderService

from utils.file_utils import JOB_SEARCH_CONFIG_FILE, read_json_file


class JobSearchService:
    """Service class for handling job applicant MCP operations"""
    
    def __init__(self, linkedin_jobs_scraper_service: LinkedInJobsScraperService, glassdoor_jobs_scraper_service: GlassdoorJobsScraperService,
                 company_mcp_service: CompanyReaderService, jobs_filter_service: JobsFilterService, jobs_saver_service:JobsSaverService):
        self.company_mcp_service = company_mcp_service
        self.linkedin_jobs_scraper_service = linkedin_jobs_scraper_service
        self.glasdoor_jobs_scraper_service = glassdoor_jobs_scraper_service
        self.jobs_filter_service = jobs_filter_service
        self.jobs_saver_service = jobs_saver_service
  

    async def search_jobs_from_internet(self, job_title: Optional[str] = None, location: Optional[str] = None, 
                                      remote: Optional[bool] = None, user_id: Optional[str] = None) -> List:
        """Search for jobs from multiple sources (LinkedIn and Glassdoor)"""
        job_title, location, remote, forbidden_titles = await self._get_search_params_from_config_or_default(
            job_title, location, remote)
        
        jobs = []
        
        # LinkedIn jobs
        linkedin_jobs = await self._run_scraper_with_filtering(
            'linkedin', self.linkedin_jobs_scraper_service, job_title, location, remote, user_id, forbidden_titles)
        if linkedin_jobs:
            jobs.extend(linkedin_jobs)

        # Glassdoor jobs
        glassdoor_jobs = await self._run_scraper_with_filtering(
            'glassdoor', self.glasdoor_jobs_scraper_service, job_title, location, remote, user_id, forbidden_titles)
        if glassdoor_jobs:
            jobs.extend(glassdoor_jobs)

        return jobs
    
    async def get_jobs_from_linkedin(self, job_title: Optional[str] = None, remote: Optional[bool] = None,
                                   user_id: Optional[str] = None) -> List:
        """Search for jobs on LinkedIn"""
        job_title, location, remote, forbidden_titles = await self._get_search_params_from_config_or_default(
            job_title, location, remote)
        return await self._run_scraper_with_filtering(
            'linkedin', self.linkedin_jobs_scraper_service, job_title, location, remote, user_id, forbidden_titles)

    async def get_jobs_from_glassdoor(self, job_title: Optional[str] = None, 
                                    location: Optional[str] = None, 
                                    remote: Optional[bool] = None, 
                                    user_id: Optional[str] = None) -> List:
        """Search for jobs on Glassdoor"""
        job_title, location, remote, forbidden_titles = await self._get_search_params_from_config_or_default(
            job_title, location, remote)

        return await self._run_scraper_with_filtering(
            'glassdoor', self.glasdoor_jobs_scraper_service, job_title, location, remote, user_id, forbidden_titles)

    async def get_user_applications_for_company(self, user_id: str, company_name: str) -> Dict[str, Any]:
        """Get all job applications for a specific user and company"""
        try:        
            return await self.company_mcp_service.get_user_applications_for_company(user_id, company_name)
        except Exception as e:
            logging.error(f"Error getting user applications: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _run_scraper_with_filtering(self, scraper_name: str, scraper: AbstractJobsScraperService, 
                                        job_title: str, location: str, remote: bool,
                                        user_id: Optional[str], forbidden_titles: List[str]) -> List:
        """Run a specific scraper and filter out applied jobs"""
        
        
        # Run the scraper
        jobs = await scraper.run_scraper(
            job_title=job_title,
            location=location,
            remote=remote,
            forbidden_titles=forbidden_titles,
            max_pages=2
        )
        
        if not jobs:
            logging.warning(f"No jobs found from {scraper_name} scraper")
            return []
        
        # Filter applied jobs
        non_applied_jobs, suspected_applied_jobs = await self.jobs_filter_service.filter_jobs(jobs, user_id)
        
        # Save filtered results
        if non_applied_jobs:
            await self.jobs_saver_service.save_jobs_to_file(
                non_applied_jobs, f'non_applied_jobs_{scraper_name}.json')
        
        if suspected_applied_jobs:
            await self.jobs_saver_service.save_jobs_to_file(
                suspected_applied_jobs, f'suspected_applied_jobs_{scraper_name}.json')
        
        logging.info(f"Found {len(non_applied_jobs)} new jobs and {len(suspected_applied_jobs)} suspected applied jobs from {scraper_name}")
        
        return non_applied_jobs

    async def _get_search_params_from_config_or_default(self, job_title: Optional[str] = None, 
                                                      location: Optional[str] = None,
                                                      remote: Optional[bool] = None) -> Tuple[str, str, bool, List[str]]:
        """Get search parameters from config or use defaults"""
        try:
            job_search_config = await read_json_file(JOB_SEARCH_CONFIG_FILE)
            logging.debug(f"job config loaded for job search defaults: {job_search_config}")
        except Exception as e:
            logging.debug(f"Could not load job config for defaults: {e}")
            job_search_config = {}

        # Use values from config when provided, otherwise use hardcoded defaults
        if job_title is None:
            job_title = job_search_config.get('job_search', {}).get('job_title', 'Software Engineer')
        if location is None:
            location = job_search_config.get('job_search', {}).get('location', 'Israel')
        
        if remote is None:
            remote_val = job_search_config.get('job_search', {}).get('remote')
            remote = bool(remote_val) if remote_val is not None else True

        # Get forbidden titles from config
        forbidden_titles = job_search_config.get('job_search', {}).get('forbidden_titles', [])
        
        return job_title, location, remote, forbidden_titles