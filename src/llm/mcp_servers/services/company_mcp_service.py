import logging

from llm.mcp_servers.persistence.mcp_company_mongo_persist import MCPCompanyMongoPersist
from llm.mcp_servers.services.models import UserApplicationResponse, UserApplication, UserApplicationResponseCode

from repository.models import PersistenceErrorCode

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

    async def get_all_user_applications(self, user_id: str) -> UserApplicationResponse:
        """
        Get all job applications for a specific user.
        """
        response = await self.mcp_company_persist.get_all_applications(user_id)
        if response.code == PersistenceErrorCode.SUCCESS:
            user_applications = [
                UserApplication(
                    company_name=app["company_name"], 
                    tracked_job=app["jobs"]
                ) for app in response.data
            ]
            return UserApplicationResponse(
                code=UserApplicationResponseCode.SUCCESS,
                user_applications=user_applications
            )
        else:
            return UserApplicationResponse(
                code=UserApplicationResponseCode.ERROR, 
                user_applications=[], 
                error_message=response.error_message or "Unknown error occurred"
            )
        
    async def get_user_applications_for_company(self, user_id: str, company_name: str) -> UserApplicationResponse:
        """
        Get all job applications for a specific user and company.
        """
        try:
            # Get the application data
            response = await self.mcp_company_persist.get_application(user_id, company_name.lower())
            
            if response.code == PersistenceErrorCode.SUCCESS:
                user_application = UserApplication(
                    company_name=response.data["company_name"],
                    tracked_job=response.data["jobs"]
                )
                return UserApplicationResponse(
                    code=UserApplicationResponseCode.SUCCESS,
                    user_applications=[user_application]
                )
            elif response.code == PersistenceErrorCode.NOT_FOUND:
                return UserApplicationResponse(
                    code=UserApplicationResponseCode.SUCCESS,
                    user_applications=[],
                    error_message="No applications found for this company"
                )
            else:
                return UserApplicationResponse(
                    code=UserApplicationResponseCode.ERROR,
                    user_applications=[],
                    error_message=response.error_message or "Unknown error occurred"
                )
        except Exception as e:
            logging.exception(f"Error in CompanyMCPService.get_user_applications_for_company: {e}")
            return UserApplicationResponse(
                code=UserApplicationResponseCode.ERROR,
                user_applications=[],
                error_message=str(e)
            )
