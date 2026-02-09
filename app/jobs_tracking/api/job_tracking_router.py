import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..api.schemas.models import TrackedJobDto

from ..services.job_tracking_read_service import JobTrackingReadService
from ..services.job_tracking_write_service import JobTrackingWriteService

from .schemas.requests import TrackNewJobRequest, TrackExistingJobRequest, GetTrackedJobsRequest, DeleteTrackedJobsRequest
from .schemas.response import CompanyTrackingApiResponseCode, CompanyApiResponse
from ..services.domain.models import JobApplicationState
from ..services.domain.results import CompanyResponse
from ..services.domain.commands import (
    TrackNewJobCommand,
    TrackExistingJobCommand,
    GetTrackedJobsCommand,
    DeleteTrackedJobsCommand,
    ExtractJobInfoCommand
)
from ...utils.utils import is_valid_uuid4
from .job_tracking_mapper import (
    api_tracked_job_to_model_tracked_job,
    api_company_list_to_domain_company_list,
    create_company_api_response
)

from ..services.job_tracking_attributes_parser import extract_job_title_and_company


from ...utils.dependency_container import Container

router = APIRouter(prefix="/api/jobs", tags=["job-tracking"])


def get_job_tracking_write_service() -> JobTrackingWriteService:
    """Dependency injection for JobTrackingWriteService"""
    return Container.get_container().job_tracking_write_service()


def get_job_tracking_read_service() -> JobTrackingReadService:
    """Dependency injection for JobTrackingReadService"""
    return Container.get_container().job_tracking_read_service()



@router.get("/application-states", response_model=List[str])
async def get_job_application_states():
    """Get list of available job application states"""
    try:
        return [state.name for state in JobApplicationState if not state == JobApplicationState.UNKNOWN]
    except Exception as e:
        logging.exception(f"Error getting job application states: {e}")
        raise HTTPException(status_code=500, detail="Error getting job application states")


@router.post("/track-new", response_model=CompanyResponse)
async def track_new_job(
    request: TrackNewJobRequest,
    job_tracking_write_service: JobTrackingWriteService = Depends(get_job_tracking_write_service)
):
    """Track a new job for a user"""
    _validate_job_parameters(request.user_id, request.company_name, request.job_dto)
    
    if not request.company_name or not request.job_dto or not request.job_dto.job_title or not request.job_dto.job_url:
        logging.error("Missing required parameter: user_id, company_name, job_dto, job url or job title")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    tracked_job = api_tracked_job_to_model_tracked_job(request.job_dto)
    
    command = TrackNewJobCommand(
        user_id=request.user_id,
        company_name=request.company_name,
        tracked_job=tracked_job
    )
    response: CompanyResponse = await job_tracking_write_service.track_new_job(command)
    return create_company_api_response(response)


@router.post("/track-existing", response_model=CompanyResponse)
async def track_existing_job(request: TrackExistingJobRequest,
                             job_tracking_write_service: JobTrackingWriteService = Depends(get_job_tracking_write_service)):
    """Track an existing job for a user"""
    _validate_job_parameters(request.user_id, request.company_name, request.job_dto)
    
    tracked_job = api_tracked_job_to_model_tracked_job(request.job_dto)
    
    command = TrackExistingJobCommand(
        user_id=request.user_id,
        company_id=request.company_id,
        tracked_job=tracked_job
    )
    response = await job_tracking_write_service.track_existing_job(command)
    return create_company_api_response(response)

@router.post("/get-tracked", response_model=CompanyResponse)
async def get_tracked_jobs(
    request: GetTrackedJobsRequest,
    job_tracking_read_service: JobTrackingReadService = Depends(get_job_tracking_read_service)
):
    """Get all tracked jobs for a company"""
    if not is_valid_uuid4(request.user_id):
        logging.error(f"Invalid user_id: '{request.user_id}' is not a valid UUID4")
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    if not request.company_name:
        logging.error("Missing required parameter: company_name")
        raise HTTPException(status_code=400, detail="Missing company_name")
    
    command = GetTrackedJobsCommand(user_id=request.user_id, company_name=request.company_name)
    company_response: CompanyResponse = await job_tracking_read_service.get_tracked_jobs(command)
    
    if company_response:
        api_response = create_company_api_response(company_response)
        if api_response.code != CompanyTrackingApiResponseCode.ERROR:
            return api_response
    
    raise HTTPException(status_code=500, detail="Error retrieving tracked jobs")


@router.get("/extract-job-info", response_model=dict)
async def extract_job_title_and_company(
    url: str
):
    """Extract job title and company from a URL"""
    if not url:
        logging.error("Missing required parameter: url")
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        command = ExtractJobInfoCommand(url=url)
        return extract_job_title_and_company(command)
    except Exception as e:
        logging.exception(f"Error extracting job info from URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract job information")


@router.post("/delete-tracked", response_model=dict)
async def delete_tracked_jobs(
    request: DeleteTrackedJobsRequest,
    job_tracking_write_service: JobTrackingWriteService = Depends(get_job_tracking_write_service)
):
    """Delete tracked jobs"""
    if not is_valid_uuid4(request.user_id):
        logging.error(f"Invalid user_id: '{request.user_id}' is not a valid UUID4")
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    if not request.companies_jobs or len(request.companies_jobs) == 0:
        logging.error("Missing required parameter: companies_jobs")
        raise HTTPException(status_code=400, detail="Missing companies_jobs")
    
    domain_companies = api_company_list_to_domain_company_list(request.companies_jobs)
    command = DeleteTrackedJobsCommand(user_id=request.user_id, companies_jobs=domain_companies)
    success = await job_tracking_write_service.delete_tracked_jobs(command)
    return {"success": success}


def _validate_job_parameters(user_id: str, company_name: str, tracked_job: TrackedJobDto):
    if not tracked_job or not user_id or not company_name or not tracked_job.job_url or not tracked_job.job_title:
        raise HTTPException(status_code=400, detail="Missing required parameters for job operation")
    
    if tracked_job.contact_name and not all(character.isalpha() or character in (' ', '-', "'") for character in tracked_job.contact_name):
        raise HTTPException(status_code=400, detail="Contact name must contain only letters")
    
    if not is_valid_uuid4(user_id):
        logging.error(f"Invalid user_id: '{user_id}' is not a valid UUID4")
        raise HTTPException(status_code=400, detail="Invalid user_id format")
