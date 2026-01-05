import pytest
from dependency_injector import containers, providers

from jobs_tracking.job_tracking_linkedin_parser import extract_linkedin_job
from llm.mcp_servers.job_search.services.job_scrapers.glassdoor_jobs_scraper_service import GlassdoorJobsScraperService
from llm.mcp_servers.job_search.services.job_scrapers.linkedin_jobs_scraper_service import LinkedInJobsScraperService
from llm.mcp_servers.job_search.models import ScrapedJob

class Container(containers.DeclarativeContainer):
    linkedin_scraper = providers.Factory(LinkedInJobsScraperService)
    glassdoor_scraper = providers.Factory(GlassdoorJobsScraperService)

@pytest.fixture
def container():
    return Container()

@pytest.fixture
def linkedin_jobs_scraper(container):
    return container.linkedin_scraper()

@pytest.fixture
def glassdoor_jobs_scraper(container):
    return container.glassdoor_scraper()

@pytest.mark.asyncio
async def test_linkedin_scraper(linkedin_jobs_scraper):
    """Test LinkedIn scraper can search for jobs"""
    job_title = "python developer"
    jobs: list[ScrapedJob] = await linkedin_jobs_scraper.run_scraper(job_title=job_title, location="Israel", max_pages=1)
    
    assert isinstance(jobs, list)
    if jobs:
        assert jobs[0].title.lower().find("python") != -1


@pytest.mark.asyncio
async def test_glassdoor_scraper(glassdoor_jobs_scraper):
    """
    Test Glassdoor scraper can search for jobs. Only test no failures
    The search internally shows irrelevant results.
    """
    jobs = await glassdoor_jobs_scraper.run_scraper(job_title="python developer", location="Israel", max_jobs_per_page=5, max_pages=1)
    
    
    assert isinstance(jobs, list)
    assert len(jobs) <= 5


@pytest.mark.asyncio
async def test_scraper_empty_query(linkedin_jobs_scraper, glassdoor_jobs_scraper):
    """Test scrapers handle empty queries gracefully"""
    linkedin_jobs = await linkedin_jobs_scraper.run_scraper("", "")
    glassdoor_jobs = await glassdoor_jobs_scraper.run_scraper("", "")
    
    assert isinstance(linkedin_jobs, list)
    assert isinstance(glassdoor_jobs, list)

def test_linkedin_job_and_company_scaper():
    url = "https://www.linkedin.com/jobs/view/4343611949/"
    result = extract_linkedin_job(url)
    assert isinstance(result, dict)
    assert "job_title" in result
    assert "company_name" in result
    
    # Verify neither job title nor company name is "N/A"
    assert result["job_title"] != "N/A"
    assert result["company_name"] != "N/A"
    
