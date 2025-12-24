import pytest
import os
from dependency_injector import containers, providers

from llm.mcp_servers.job_search.services.glassdoor_jobs_scraper import GlassdoorJobsScraper
from llm.mcp_servers.job_search.services.linkedin_jobs_scraper import LinkedInJobsScraper
from llm.mcp_servers.job_search.models import ScrapedJob

class Container(containers.DeclarativeContainer):
    linkedin_scraper = providers.Factory(LinkedInJobsScraper)
    glassdoor_scraper = providers.Factory(GlassdoorJobsScraper)

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
    jobs: list[ScrapedJob] =  linkedin_jobs_scraper.run_scraper(job_title=job_title, location="Israel", max_pages=1)
    
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
    assert len(jobs) <=5


@pytest.mark.asyncio
async def test_scraper_empty_query(linkedin_jobs_scraper, glassdoor_jobs_scraper):
    """Test scrapers handle empty queries gracefully"""
    linkedin_jobs = linkedin_jobs_scraper.run_scraper("", "")
    glassdoor_jobs = await glassdoor_jobs_scraper.run_scraper("", "")
    
    assert isinstance(linkedin_jobs, list)
    assert isinstance(glassdoor_jobs, list)

