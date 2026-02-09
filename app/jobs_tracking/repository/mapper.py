import uuid
from datetime import datetime, timezone
from bson import ObjectId

from ..services.domain.enums import JobApplicationState


from ..services.domain.models import Company, TrackedJob
from .models.entities import JobEntity, CompanyEntity

class EntitiesMapper:
    """Handles conversions between Domain models, Persistence Entities, and MongoDB documents."""

    @staticmethod
    def mongo_dict_to_company_entity(data: dict) -> CompanyEntity:
        """Helper to convert raw MongoDB dict (with $oid and $date) to Entity"""
        return CompanyEntity(
            company_id=data["company_id"],
            company_name=data["company_name"],
            user_id=data["user_id"],
            jobs=[
                JobEntity(
                    job_id = job["job_id"] if job.get("job_id") else str(uuid.uuid4()),
                    job_url=job["job_url"],
                    job_title=job["job_title"],
                    job_state=job["job_state"],
                    # Handling the MongoDB $date format
                    update_time=job["update_time"] if isinstance(job["update_time"], datetime) 
                                else datetime.fromisoformat(job["update_time"]["$date"].replace("Z", "+00:00")),
                    contact_name=job.get("contact_name"),
                    contact_url=job.get("contact_url"),
                    contact_linkedin=job.get("contact_linkedin"),
                    contact_email=job.get("contact_email")
                ) for job in data.get("jobs", [])
            ]
        )


    @staticmethod
    def domain_job_to_entity_job(domain: TrackedJob) -> JobEntity:
        """
        Converts a Domain model to a Persistence Entity.
        Handles the injection of missing IDs or timestamps if they don't exist yet.
        """
        return JobEntity(
            job_id=domain.job_id or str(uuid.uuid4()),
            job_url=domain.job_url,
            job_title=domain.job_title,
            job_state=str(domain.job_state),  # Convert Enum to string for DB
            update_time=domain.update_time or datetime.now(timezone.utc),
            contact_name=domain.contact_name,
            contact_linkedin=domain.contact_linkedin,
            contact_email=domain.contact_email,
        )

    
    @staticmethod
    def entity_job_to_domain_job(entity: JobEntity) -> TrackedJob:
        """Converts a Persistence Entity to a Domain model."""
        return TrackedJob(
            job_id=entity.job_id,
            job_url=entity.job_url,
            job_title=entity.job_title,
            job_state=JobApplicationState(entity.job_state),
            update_time=entity.update_time,
            contact_name=entity.contact_name,
            contact_linkedin=entity.contact_linkedin,
            contact_email=entity.contact_email
        )

    @staticmethod
    def entity_company_to_domain_company(entity: CompanyEntity) -> Company:
        """Converts a Persistence Entity to a Domain model."""
        return Company(
            company_id=entity.company_id,
            company_name=entity.company_name,
            tracked_jobs=[EntitiesMapper.entity_job_to_domain_job(job) for job in entity.jobs]
        )
