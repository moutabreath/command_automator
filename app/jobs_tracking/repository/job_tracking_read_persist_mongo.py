import logging
import pymongo.errors as mongo_errors

from ..services.domain.models import Company

from .abstract_job_tracking_persist_mongo import AbstractJobTrackingPersistMongo


from .mapper import EntitiesMapper
from .models.queries import GetTrackedJobsQuery


from ...repository.models import PersistenceErrorCode, PersistenceResponse

class JobTrackingReadPersistMongo(AbstractJobTrackingPersistMongo):

  
    async def get_tracked_jobs(self, query: GetTrackedJobsQuery) -> PersistenceResponse[Company]:        
        """Get all application by user and company"""
        user_id, company_name = query.user_id, query.company_name
        try:
            result_dict = await self.job_applications.find_one({
                "user_id": user_id, "company_name": company_name
            })
            
            if result_dict is None:
                return PersistenceResponse(data=None, code=PersistenceErrorCode.NOT_FOUND)


            company_entity = EntitiesMapper.mongo_dict_to_company_entity(result_dict)
            company = EntitiesMapper.entity_company_to_domain_company(company_entity)
        
            return PersistenceResponse(
                id=company_entity.company_id, 
                data=company, 
                code=PersistenceErrorCode.SUCCESS
            )
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.CONNECTION_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )

    async def get_all_applications(self, user_id: str) -> PersistenceResponse[list[Company]]:
        """Get all applications for a user"""
        try:
            cursor = self.job_applications.find({"user_id": user_id})
            # 1. Fetch raw dictionaries from the cursor
            results_dicts = await cursor.to_list(length=None)
            if not results_dicts:
                return PersistenceResponse(data=[], code=PersistenceErrorCode.SUCCESS)

            # Map the first document to our root Entity
            company_entity = EntitiesMapper.mongo_dict_to_company_entity(results_dicts[0])

            # 3. Transform into the Company domain model
            data = [
                Company(
                    company_id=company_entity.company_id,
                    company_name=company_entity.company_name,
                    job=EntitiesMapper.entity_job_to_domain_job(job_entity)
                )
                for job_entity in company_entity.jobs
            ]

            return PersistenceResponse(
                data=data,
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
        
 # ==================== QUERY HELPERS ====================
    
    async def get_jobs_by_state(self, user_id: str, state: str) -> PersistenceResponse[list[dict]]:
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
            results = await self.job_applications.aggregate(pipeline).to_list(length=None)
            return PersistenceResponse(data=results, code=PersistenceErrorCode.SUCCESS)
        except mongo_errors.OperationFailure as e:
            logging.exception(f"MongoDB operation failed: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.OPERATION_ERROR, error_message=str(e))
        except mongo_errors.ConnectionFailure as e:
            logging.exception(f"MongoDB connection failed: {e}")
            return PersistenceResponse(
                data=None,
                code=PersistenceErrorCode.CONNECTION_ERROR,
                error_message=f"MongoDB connection failed: {e}"
            )
        except Exception as e:
            logging.exception(f"MongoDB encountered an unknown error: {e}")
            return PersistenceResponse(data=None, code=PersistenceErrorCode.UNKNOWN_ERROR, error_message=str(e))
    
    async def get_recent_jobs(self, user_id: str, limit: int = 10) -> PersistenceResponse[list[dict]]:
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
            results = await self.job_applications.aggregate(pipeline).to_list(length=None)
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

    
    async def _execute_job_aggregation(self, pipeline: list[dict]) -> PersistenceResponse[list[dict]]:
        """Execute aggregation pipeline and convert results to dictionary list"""
        try:
            cursor = self.job_applications.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            tracked_jobs_dicts = [r["job"] for r in results]
            return PersistenceResponse(data=tracked_jobs_dicts, code=PersistenceErrorCode.SUCCESS)
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
    
