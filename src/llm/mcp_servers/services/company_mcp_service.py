import logging
from typing import Dict, Any
from llm.mcp_servers.persistence.mcp_company_mongo_persist import MCPCompanyMongoPersist
from repository.abstract_mongo_persist import PersistenceErrorCode

class CompanyMCPService:
    
    def __init__(self, company_persist: MCPCompanyMongoPersist):
        self.mcp_company_persist = company_persist

    async def initialize(self):
        """
        Initialize the service and its dependencies.
        """
        try:
            await self.mcp_company_persist.initialize_connection()
            logging.info("CompanyMCPService initialized successfully.")
        except Exception as e:
            logging.exception(f"Error in CompanyMCPService.initialize: {e}")
            raise

    async def get_user_applications_for_company(self, user_id: str, company_name: str) -> Dict[str, Any]:
        """
        Get all job applications for a specific user and company.
        """
        try:
            # Get the application data
            response = await self.mcp_company_persist.get_application(user_id, company_name.lower())
            
            if response.code == PersistenceErrorCode.SUCCESS:
                return {
                    "success": True,
                    "company_name": company_name,
                    "user_id": user_id,
                    "application_data": response.data
                }
            elif response.code == PersistenceErrorCode.NOT_FOUND:
                return {
                    "success": True,
                    "company_name": company_name,
                    "user_id": user_id,
                    "application_data": None,
                    "message": "No applications found for this company"
                }
            else:
                return {
                    "success": False,
                    "error": response.error_message or "Unknown error occurred"
                }
        except Exception as e:
            logging.exception(f"Error in CompanyMCPService.get_user_applications_for_company: {e}")
            return {
                "success": False,
                "error": str(e)
            }
