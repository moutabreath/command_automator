import logging
from typing import List, Dict
import pymongo.errors as mongo_errors

from motor.motor_asyncio import AsyncIOMotorClient

from repository.abstract_mongo_persist import PersistenceErrorCode, PersistenceResponse

class MongoCompanyPersist:
    def __init__(self, connection_string: str, db_name: str):
        self.connection_string = connection_string
        self.db_name = db_name
        
        # State indicators
        self.async_client = None
        self.async_db = None
        logging.getLogger("pymongo").setLevel(logging.WARNING)

    
    async def initialize_connection(self):
        """
        Internal initialization logic. 
        """

        self.async_client = AsyncIOMotorClient(
            self.connection_string
        )
        self.async_client._serializable = False
        
        self.async_db = self.async_client[self.db_name]
        self.async_db._serializable = False        
        
        self.job_applications = self.async_db.job_applications
   
  
    async def get_application(self, user_id: str, company_name: str) -> PersistenceResponse[Dict]:
        """Get application by user and company"""
        try:
            result = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name.lower()
                })
            if result:
                return PersistenceResponse(
                    data=result,
                    code=PersistenceErrorCode.SUCCESS
                )
            logging.error(f"Document not found {user_id}, {company_name}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.NOT_FOUND,
                error_message=f"Document with id {user_id} and company name {company_name} not found"
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    async def get_all_applications(self, user_id: str) -> PersistenceResponse[List[Dict]]:
        """Get all applications for a user"""
        try:
            cursor = self.job_applications.find({"user_id": user_id})
            results = await cursor.to_list(length=None)
            return PersistenceResponse(
                data=results,
                code=PersistenceErrorCode.SUCCESS
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
   
    async def get_jobs(self, user_id: str, company_name: str) -> PersistenceResponse[List[Dict]]:
        """Get all jobs for a company"""
        try:
            app_response = await self.get_application(user_id, company_name)
            if app_response.code == PersistenceErrorCode.SUCCESS and app_response.data:
                return PersistenceResponse(data=app_response.data.get("jobs", []), code=PersistenceErrorCode.SUCCESS)
            elif app_response.code == PersistenceErrorCode.NOT_FOUND:
                return PersistenceResponse(data=[], code=PersistenceErrorCode.NOT_FOUND) # Return empty list if company not found
            return app_response # Propagate other errors
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
   
    # ==================== QUERY HELPERS ====================
    
    def get_jobs_by_state(self, user_id: str, state: str) -> PersistenceResponse[List[Dict]]:
        """Get all jobs with a specific state across all companies"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$match": {"jobs.state": state}},
            {"$project": {
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        try:
            results = list(self.job_applications.aggregate(pipeline))
            return PersistenceResponse(data=results, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    def get_recent_jobs(self, user_id: str, limit: int = 10) -> PersistenceResponse[List[Dict]]:
        """Get most recently updated jobs"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$jobs"},
            {"$sort": {"jobs.update_time": -1}},
            {"$limit": limit},
            {"$project": {
                "company_name": 1,
                "job": "$jobs"
            }}
        ]
        try:
            results = list(self.job_applications.aggregate(pipeline))
            return PersistenceResponse(data=results, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))


    async def _find_existing_application(self, user_id, company_name, job_url):
        try:
            # Check if job already exists
            existing = await self.job_applications.find_one({
                "user_id": user_id,
                "company_name": company_name,
                "jobs.job_url": job_url
            })
            return existing
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            raise
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logging.exception(f"Unexpected error in add_job: {e}")
            raise 
