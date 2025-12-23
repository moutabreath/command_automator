import pytest
from user.services.user_registry_service import UserRegistryService
from jobs_tracking.services.job_tracking_service import JobTrackingService, JobTrackingResponseCode, TrackedJob
from jobs_tracking.services.models import JobApplicationState, JobTrackingResponse

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

@pytest.mark.asyncio
async def test_track_and_retrieve_job(user_service, job_service):
    # 1. Register
    email = "dummy.user@example.com"
    auth_res = await user_service.login_or_register_user_async(email)
    user_id = auth_res.user_id
    
    # 2. Track
    company = "Dummy Company"
    position = "Software Engineer"
    status = JobApplicationState.APPLIED
    url = "http://dummy.company/jobs/1"
    
    contact_name="John"
    contact_linkedin="linkedin.com/john"
    contact_email="john@example.com"
    tracked_job = TrackedJob(
        job_url=url,
        job_title=position,
        job_state=status,
        contact_name=contact_name,
        contact_linkedin=contact_linkedin,
        contact_email=contact_email
    )
    job_res: JobTrackingResponse = await job_service.add_or_update_position_async(
        user_id=user_id,
        company_name=company,
        tracked_job=tracked_job
    )
    
    # Validate job_res has valid response
    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK
    assert job_res.job is not None
    assert job_res.job.job_title == position
    assert job_res.job.job_url == url
    assert job_res.job.job_state == status
    assert job_res.job.contact_name == contact_name
    assert job_res.job.contact_linkedin == contact_linkedin
    assert job_res.job.contact_email == contact_email

@pytest.mark.asyncio
async def test_get_applications(user_service, job_service):
    # 1. Register user and add job
    email = "test.user@example.com"
    auth_res = await user_service.login_or_register_user_async(email)
    user_id = auth_res.user_id
    
    company = "Test Company"
    position = "Developer"
    
    tracked_job = TrackedJob(
        job_url="http://test.com/job",
        job_title=position,
        job_state=JobApplicationState.APPLIED,
        contact_name="Jane",
        contact_linkedin="linkedin.com/jane",
        contact_email="jane@test.com"
    )
    await job_service.add_or_update_position_async(
        user_id=user_id,
        company_name=company,
        tracked_job=tracked_job
    )
    
    # 2. Test job retrieval
    positions = await job_service.get_positions_async(user_id, company)
    assert positions is not None
    assert positions.code == JobTrackingResponseCode.OK
    assert len(positions.jobs) == 1
    assert positions.jobs[0].job_title == position

