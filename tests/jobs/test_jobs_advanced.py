import pytest
from user.services.user_registry_service import UserRegistryService
from jobs_tracking.services.job_tracking_service import JobTrackingService, JobTrackingResponseCode
from jobs_tracking.services.models import JobApplicationState, JobAndCompanyTrackingResponse, TrackedJob

from tests.mockups.mongo_mockups import MockCompanyMongoPersist, MockUserMongoPersist
import mongomock

@pytest.fixture
def db():
    return mongomock.MongoClient().job_tracker_test

@pytest.fixture(autouse=True)
def cleanup_db(db):
    """Clean up database after each test"""
    yield  # This runs the test
    # Cleanup after test
    db.users.drop()
    db.job_applications.drop()


@pytest.fixture
def user_service(db):
    mock_persist = MockUserMongoPersist(db)
    return UserRegistryService(mock_persist)

@pytest.fixture
def job_service(db):
    mock_persist = MockCompanyMongoPersist(db)
    return JobTrackingService(mock_persist)

job_link = "https://www.linkedin.com/jobs/view/4324949336"
job_state = "applied"
company_name = "finonex"
job_title = "senior backend software engineer"
contact_name = "amirdar"
contact_linkedin = "https://www.linkedin.com/in/amirdar/"

contact_name2 = "tal druckmann"
contact_linkedin2 = "https://www.linkedin.com/in/tal-druckmann-88489520/"


@pytest.mark.asyncio
async def test_update_track_and_retrieve_from_text_without_other_linkedin_format(user_service, job_service):
    text = f"""{job_link}
{company_name}
{contact_linkedin2}
{job_state}
{job_title}
{contact_name2}
"""
    job_res: JobAndCompanyTrackingResponse = await _update_track_and_retrieve_from_text(text=text, user_service=user_service, job_service=job_service)

    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK

    assert job_res.job is not None

    assert job_res.company_name == company_name
    assert job_res.job.job_url == job_link
    assert job_res.job.job_state == JobApplicationState.APPLIED    
    assert job_res.job.job_title == job_title
    assert job_res.job.contact_name == contact_name2
    assert job_res.job.contact_linkedin == contact_linkedin2


@pytest.mark.asyncio
async def test_update_track_and_retrieve_from_text_without_email(user_service, job_service):
    text = f"""{job_link}
{company_name}
{contact_linkedin}
{job_state}
{job_title}
{contact_name}
"""
    job_res: JobAndCompanyTrackingResponse = await _update_track_and_retrieve_from_text(text=text, user_service=user_service, job_service=job_service)

    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK

    assert job_res.job is not None

    assert job_res.company_name == company_name
    assert job_res.job.job_url == job_link
    assert job_res.job.job_state == JobApplicationState.APPLIED    
    assert job_res.job.job_title == job_title
    assert job_res.job.contact_name == contact_name
    assert job_res.job.contact_linkedin == contact_linkedin

    
@pytest.mark.asyncio
async def test_update_track_and_retrieve_from_text_without_title(user_service, job_service):

    text = f"""{job_link}
        {company_name}
        {contact_linkedin}
        {job_state}
        {contact_name}
        """
    job_res: JobAndCompanyTrackingResponse = await _update_track_and_retrieve_from_text(text=text, user_service=user_service, job_service=job_service)

  
    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK

    assert job_res.job is not None

    assert job_res.company_name == company_name
    assert job_res.job.job_url == job_link
    assert job_res.job.job_state == JobApplicationState.APPLIED    
    assert job_res.job.job_title == "Unknown Position"
    assert job_res.job.contact_name == contact_name
    assert job_res.job.contact_linkedin == contact_linkedin

    
@pytest.mark.asyncio
async def test_update_track_and_retrieve_from_text_without_status(user_service, job_service):
    text = f"""{job_link}
            {company_name}
            {contact_linkedin}
            {job_title}
            {contact_name}"""
    job_res = await _update_track_and_retrieve_from_text(text=text, user_service=user_service, job_service=job_service)
    
    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK

    assert job_res.job is not None

    assert job_res.company_name == company_name
    assert job_res.job.job_url == job_link
    assert job_res.job.job_state == JobApplicationState.UNKNOWN    
    assert job_res.job.job_title == job_title
    assert job_res.job.contact_name == contact_name
    assert job_res.job.contact_linkedin == contact_linkedin

async def _update_track_and_retrieve_from_text(text, job_service, user_service):

    # 1. Register user and add job
    email = "test.user@example.com"
    auth_res = await user_service.login_or_register_user_async(email)
    user_id = auth_res.user_id

    return await job_service.track_positions_from_text_async(
        user_id=user_id,
        text= text
    )