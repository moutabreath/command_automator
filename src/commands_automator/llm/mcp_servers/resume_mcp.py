import logging
import multiprocessing
from mcp.server.fastmcp import FastMCP

from commands_automator.llm.mcp_servers.resume_data import ResumeData
from commands_automator.llm.mcp_servers.services.resume_loader_service import ResumeLoaderService

# Initialize FastMCP
mcp = FastMCP("resume_fetcher")

resume_loader_service: ResumeLoaderService = None

@mcp.tool()
async def get_resume_files() -> ResumeData:
    """
    Fetch resume file, applicant name, job description and guidelines

    """    
    global resume_loader_service
    try:
        resume_content, applicant_name = await resume_loader_service.get_resume()
        if resume_content is None or applicant_name is None:
            raise ValueError("Resume content or applicant name is missing")

        guide_lines = await resume_loader_service.get_main_part_guide_lines()
        if guide_lines is None:
            guide_lines = ""  # Default empty string if guidelines not found
        else:
            guide_lines = guide_lines.replace('***applicant_name***', applicant_name)

        highlighted_sections = await resume_loader_service.get_highlighted_sections()
        if highlighted_sections is None:
            highlighted_sections = []  # Default empty list if sections not found

        job_description_content = await resume_loader_service.get_job_description()
        if job_description_content is None:
            job_description_content = ""  # Default empty string if job description not found

        cover_letter_guide_lines = await resume_loader_service.get_cover_letter_guide_lines()
        if cover_letter_guide_lines is None:
            cover_letter_guide_lines = ""  # Default empty string if cover letter guidelines not found

        # Create dictionary first to validate data
        data_dict = {
            "applicant_name": applicant_name or "",
            "general_guidelines": guide_lines or "",
            "resume": resume_content or "",
            "resume_highlighted_sections": highlighted_sections or [],
            "job_description": job_description_content or "",
            "cover_letter_guidelines": cover_letter_guide_lines or ""
        }
        logging.debug(f"Creating ResumeData with: {data_dict}")
        
        resume_data = ResumeData(**data_dict)
        logging.debug(f"Created ResumeData successfully: {resume_data.model_dump()}")
        return resume_data
    except Exception as ex:
        logging.error(f"Error fetching resume: {ex}")
        return ResumeData(
            applicant_name="",
            general_guidelines="",
            resume="",
            resume_highlighted_sections=[],
            job_description="",
            cover_letter_guidelines=""
        )


# Run the server with streamable-http transport
class MCPRunner:
 
    def init_mcp(self):
        self.mcp_process = multiprocessing.Process(target=self.run_mcp)
        self.mcp_process.start()
        
    def stop_mcp(self):
        """Cleanup method to terminate the MCP process when the agent is destroyed"""
        if hasattr(self, 'mcp_process') and self.mcp_process.is_alive():
            self.mcp_process.terminate()
            self.mcp_process.join()


    def run_mcp(self):
        global resume_loader_service
        resume_loader_service = ResumeLoaderService()
    
        # Set server configuration through the settings property
        mcp.settings.mount_path = "/mcp"
        mcp.settings.port = 8765
        mcp.settings.host = "127.0.0.1"
        
        # Run the server with streamable-http transport
        logging.debug(f"Starting MCP server at http://{mcp.settings.host}:{mcp.settings.port}{mcp.settings.mount_path}")
        mcp.run(transport="streamable-http")

    def __enter__(self):  
        return self  

    def __exit__(self, exc_type, exc_val, exc_tb):  
        self.stop_mcp()  

if __name__ == '__main__':
    mcp_runner = MCPRunner()
    mcp_runner.init_mcp()