from dataclasses import dataclass

from ...services.domain.models import TrackedJob

@dataclass(frozen=True)
class JobWithCompanyContext:
    company_id: str
    company_name: str
    job: TrackedJob

    @classmethod
    def from_mongo(cls, data: dict):
        """Maps the MongoDB aggregation result to this dataclass"""
        return cls(
            company_id=str(data["company_id"]),
            company_name=data["company_name"],
            # Leverage your existing from_dict logic for the inner job
            job=TrackedJob.from_dict(data["job"])
        )