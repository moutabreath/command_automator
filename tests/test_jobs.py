import pytest
from user.services.user_registry_service import UserRegistryService
from jobs_tracking.services.job_tracking_service import JobTrackingService, JobTrackingResponseCode
from jobs_tracking.models import JobApplicationState

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
async def test_track_and_retrieve_dummy_job(user_service, job_service, db):
    # 1. Register
    email = "dummy.user@example.com"
    auth_res = await user_service.login_or_register_user_async(email)
    user_id = auth_res.user_id
    
    # 2. Track
    company = "Dummy Company"
    position = "Software Engineer"
    status = JobApplicationState.APPLIED
    url = "http://dummy.company/jobs/1"
    
    job_res = await job_service.add_or_update_position_async(
        user_id=user_id,
        company_name=company,
        job_url=url,
        job_title=position,
        job_state=status,
        contact_name="John",
        contact_linkedin="linkedin.com/john",
        contact_email="john@example.com"
    )
    
    # Validate job_res has valid response
    assert job_res is not None
    assert job_res.code == JobTrackingResponseCode.OK
    assert job_res.job is not None
    assert job_res.job['job_title'] == position
    assert job_res.job['job_url'] == url
    assert job_res.job['job_state'] == status.value
    assert job_res.job['contact_name'] == "John"

@pytest.mark.asyncio
async def test_get_applications(user_service, job_service):
    # 1. Register user and add job
    email = "test.user@example.com"
    auth_res = await user_service.login_or_register_user_async(email)
    user_id = auth_res.user_id
    
    company = "Test Company"
    position = "Developer"
    
    await job_service.add_or_update_position_async(
        user_id=user_id,
        company_name=company,
        job_url="http://test.com/job",
        job_title=position,
        job_state=JobApplicationState.APPLIED,
        contact_name="Jane",
        contact_linkedin="linkedin.com/jane",
        contact_email="jane@test.com"
    )
    
    # 2. Test job retrieval
    positions = await job_service.get_positions(user_id, company)
    assert positions is not None
    assert positions.code == JobTrackingResponseCode.OK
    assert len(positions.jobs) == 1
    assert positions.jobs[0]['job_title'] == position