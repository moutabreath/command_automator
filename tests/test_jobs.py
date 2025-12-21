import pytest
import mongomock

from user.services.user_registry_service import UserRegistryService
from jobs_tracking.services.job_tracking_service import JobTrackingService, JobTrackingResponseCode
from jobs_tracking.models import JobApplicationState

from tests.mockups.mongo_mockups import MockCompanyMongoPersist, MockUserMongoPersist


@pytest.fixture
def user_service(db):
    mock_persist = MockUserMongoPersist(db)
    return UserRegistryService(mock_persist)

@pytest.fixture
def job_service(db):
    mock_persist = MockCompanyMongoPersist(db)
    return JobTrackingService(mock_persist)

def test_track_and_retrieve_dummy_job(user_service, job_service, db):
    # 1. Register
    email = "dummy.user@example.com"
    auth_res = user_service.login_or_register(email)
    user_id = auth_res.user_id
    
    # 2. Track
    company = "Dummy Company"
    position = "Software Engineer"
    status = JobApplicationState.APPLIED
    url = "http://dummy.company/jobs/1"
    
    job_res = job_service.add_or_update_position(
        user_id=user_id,
        company_name=company,
        job_url=url,
        job_title=position,
        job_state=status,
        contact_name="John",
        contact_linkedin="linkedin.com/john",
        contact_email="john@example.com"
    )
    
    assert job_res.code == JobTrackingResponseCode.OK
    assert job_res.job['job_title'] == position
    
    # 3. Ensure you can retrieve it
    saved_app = db.job_applications.find_one({"user_id": user_id, "company_name": "dummy company"})
    assert saved_app is not None
    assert len(saved_app['jobs']) == 1
    assert saved_app['jobs'][0]['job_title'] == position
    assert user_id is not None
    assert len(user_id) > 0
    
    # Verify persistence
    saved_user = api.db.users.find_one({'email': email})
    assert saved_user is not None
    assert str(saved_user['_id']) == user_id

def test_track_and_retrieve_dummy_job(api):
    """Test tracking a dummy job and ensuring it can be retrieved."""
    # 1. Register a user
    email = "dummy.user@example.com"
    auth_res = api.login_or_register(email)
    user_id = auth_res['text']
    
    # 2. Track a dummy job
    company = "Dummy Company"
    position = "Software Engineer"
    status = "APPLIED"
    url = "http://dummy.company/jobs/1"
    
    job_res = api.track_job_application(
        user_id=user_id,
        company=company,
        url=url,
        title=position,
        status=status
    )
    
    assert job_res['code'] == 'OK'
    assert '_id' in job_res
    assert job_res['company'] == company
    job_id = job_res['_id']
    
    # 3. Ensure you can retrieve it
    retrieved_job = api.get_job(job_id)
    
    assert retrieved_job is not None
    assert retrieved_job['_id'] == job_id
    assert retrieved_job['company'] == company
    assert retrieved_job['position_title'] == position
    assert retrieved_job['user_id'] == user_id