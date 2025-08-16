import logging
import multiprocessing
from mcp.server.fastmcp import FastMCP

from llm.mcp_servers.resume_data import ResumeData
from llm.mcp_servers.services.resume_loader_service import ResumeLoaderService

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

        guide_lines = await resume_loader_service.get_main_part_guide_lines()
        guide_lines = guide_lines.replace('***applicant_name***', applicant_name)

        highlighted_sections = await resume_loader_service.get_highlighted_sections()

        job_description_content = await resume_loader_service.get_job_description()

        cover_letter_guide_lines = await resume_loader_service.get_cover_letter_guide_lines()

        resume_data: ResumeData = ResumeData(
                                            applicant_name = applicant_name,
                                            general_guidelines=guide_lines,
                                            resume=resume_content, 
                                            resume_highlighted_sections=highlighted_sections,
                                            job_description=job_description_content,
                                            cover_letter_guidelines=cover_letter_guide_lines)

        return resume_data
    except Exception as ex:
        logging.error(f"Error fetching resume: {ex}")
        return None


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