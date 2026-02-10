from mcp.server.fastmcp import FastMCP

from ..setup.mcp_dependency_container import MCPContainer
from ..resume import ResumeData


# Initialize FastMCP
mcp = FastMCP("job_applicant_helper")

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """Fetch resume file, applicant name, job description and guidelines"""
    return await MCPContainer.get_container().resume_loader_service().get_resume_files()

@mcp.tool()
async def search_jobs_on_the_internet(job_title: str | None = None, location: str | None = None,
                                      remote: bool | str | None = None,
                                      user_id: str | None = None) -> list:
    """Search for jobs from multiple sources (LinkedIn and Glassdoor)"""
    job_search_service = MCPContainer.get_container().job_search_service()
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.search_jobs_from_internet(job_title, location, remote, user_id)
    
@mcp.tool()
async def get_jobs_from_linkedin(job_title: str | None = None, location: str | None = None,
    remote: bool | str | None = None, user_id: str | None = None) -> list:
    """Search for jobs on LinkedIn"""
    job_search_service = MCPContainer.get_container().job_search_service()
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.get_jobs_from_linkedin(job_title, location, remote, user_id)

@mcp.tool()
async def get_jobs_from_glassdoor(job_title: str | None = None, location: str | None = None, 
                                  remote: bool | str | None = None, user_id: str | None = None) -> list:
    """Search for jobs on Glassdoor"""
    job_search_service = MCPContainer.get_container().job_search_service()
    if isinstance(remote, str):
        remote = remote.lower() in ('true', '1', 'yes', 'on')
    return await job_search_service.get_jobs_from_glassdoor(job_title, location, remote, user_id)

@mcp.tool()
async def get_user_applications_for_company(user_id: str, company_name: str) -> dict:    
    """Get all job applications for a specific user and company"""
    return await MCPContainer.get_container().job_search_service().get_user_applications_for_company(user_id, company_name)
