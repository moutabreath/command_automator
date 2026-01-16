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


@pytest.fixture
def sample_job():
    return TrackedJob(
        job_id="job1",
        job_url="https://linkedin.com/jobs/view/123",
        job_title="Software Engineer",
        job_state=JobApplicationState.APPLIED,
        contact_name="John Doe",
        contact_email="john@example.com"
    )


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
    job_res: JobTrackingResponse = await job_service.track_new_job_async(
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
    await job_service.track_new_job_async(
        user_id=user_id,
        company_name=company,
        tracked_job=tracked_job
    )
    
    # 2. Test job retrieval
    company_response = await job_service.get_tracked_jobs_async(user_id, company)
    assert company_response is not None
    assert company_response.code == JobTrackingResponseCode.OK
    assert len(company_response.company.tracked_jobs) == 1
    assert company_response.company.tracked_jobs[0].job_title == position


@pytest.mark.asyncio
async def test_track_new_job_missing_params(job_service, sample_job):
    """Test validation for missing parameters."""
    # Missing user_id
    response = await job_service.track_new_job("", "Acme", sample_job)
    assert response.code == JobTrackingResponseCode.ERROR

    # Missing company_name
    response = await job_service.track_new_job("user1", "", sample_job)
    assert response.code == JobTrackingResponseCode.ERROR

    # Missing job_url
    sample_job.job_url = ""
    response = await job_service.track_new_job("user1", "Acme", sample_job)
    assert response.code == JobTrackingResponseCode.ERROR

@pytest.mark.asyncio
async def test_track_new_job_invalid_contact_name(job_service, sample_job):
    """Test validation for invalid contact name."""
    sample_job.contact_name = "John123" # Contains numbers
    response = await job_service.track_new_job("user1", "Acme", sample_job)
    
    assert response.code == JobTrackingResponseCode.ERROR
    assert response.job == sample_job

@pytest.mark.asyncio
async def test_track_new_job_persistence_failure(job_service, sample_job):
    """Test handling of persistence layer failure."""

    response = await job_service.track_new_job("user1", "Acme", sample_job)

    assert response.code == JobTrackingResponseCode.ERROR


@pytest.mark.asyncio
async def test_track_existing_job_async_success(job_service, sample_job):
    """Test successful job update."""

    response = await job_service.trackg_existing_job("user1", "Acme Corp", sample_job)

    assert response.code == JobTrackingResponseCode.OK
    assert response.job.job_title == "Updated Title"

@pytest.mark.asyncio
async def test_track_existing_job_async_missing_params(job_service, sample_job):
    """Test validation for missing parameters in update."""
    response = await job_service.track_existing_job_async("user1", "", sample_job)
    assert response.code == JobTrackingResponseCode.ERROR

@pytest.mark.asyncio
async def test_track_existing_job_async_not_found(job_service, sample_job):
    """Test handling when job to update is not found."""

    response = await job_service.track_existing_job_async("user1", "Acme", sample_job)

    assert response.code == JobTrackingResponseCode.ERROR
