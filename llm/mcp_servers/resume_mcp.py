from mcp.server.fastmcp import FastMCP

from llm.mcp_servers.resume_data import ResumeData
from llm.mcp_servers.services.resume_loader_service import ResumeLoaderService


# Initialize FastMCP
mcp = FastMCP("resume_fetcher")

resume_loader_service: ResumeLoaderService = ResumeLoaderService()

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines

    """
    resume_data: ResumeData = ResumeData()

    resume_content, applicant_name = await resume_loader_service.get_resume()
    resume_data.resume = resume_content

    guide_lines = await resume_loader_service.get_main_part_guide_lines()
    guide_lines = guide_lines.replace('***applicant_name***', applicant_name)
    resume_data.general_guidelines = guide_lines

    highlighted_sections = await resume_loader_service.get_highlighted_sections()
    resume_data.resume_highlighted_sections = highlighted_sections

    job_desc_content = await resume_loader_service.get_job_description()
    resume_data.job_desc = job_desc_content

    cover_letter_guide_lines = await resume_loader_service.get_cover_letter_guide_lines()
    resume_data.cover_letter_guidelines = cover_letter_guide_lines

    return resume_data

# Run the server with streamable-http transport
def run_mcp():
    # Set server configuration through the settings property
    mcp.settings.mount_path = "/mcp"
    mcp.settings.port = 8765
    mcp.settings.host = "127.0.0.1"
    
    # Run the server with streamable-http transport
    print(f"Starting MCP server at http://{mcp.settings.host}:{mcp.settings.port}{mcp.settings.mount_path}")
    mcp.run(transport="streamable-http")