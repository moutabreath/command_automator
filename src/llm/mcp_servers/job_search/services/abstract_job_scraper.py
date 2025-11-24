from datetime import datetime
import logging

from llm.mcp_servers.job_search.models import Job
from llm.mcp_servers.services.shared_service import SharedService

from ..utils.time_parser import parse_time_expression

class AbstractJobScraper(SharedService):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def validate_job(self, job_data, forbidden_titles):
        """Validate job data against forbidden titles"""
        # Required fields for Job model (job_data may use 'url' key for link)
        required_keys = ['title', 'company', 'location', 'description', 'url', 'posted_date']

        job_description_dict = self._init_job_description_dict(job_data, required_keys)

        # Filter out undesired titles early, but guard if title isn't a string
        try:
            title_text = str(job_description_dict.get('title') or '')
        except Exception:
            title_text = ''
        if any(ft.lower() in title_text.lower() for ft in (forbidden_titles or [])):
            return None

        # Prepare fields for Job construction and handle posted_date parsing
        parsed_date = self._calc_date_from_range(job_description_dict.get('posted_date'))         

        # Try to build a Job; on ValidationError, create fallbacks per-field
        try:
            return Job(
                title=str(job_description_dict.get('title')),
                company=str(job_description_dict.get('company')),
                location=str(job_description_dict.get('location')),
                description=(None if job_description_dict.get('description') in (None, False, "N/A", "") else str(job_description_dict.get('description'))),
                link=job_description_dict.get('url'),
                posted_date=parsed_date
            )
        except Exception as e:
            return self._construct_fallback_job(job_description_dict, parsed_date, e)
            
    def _init_job_description_dict(self, job_data, required_keys):
        # Make a shallow copy and ensure required keys exist; if missing, replace
        # with a descriptive placeholder so we can still return a Job object.
        job_description_dict = dict(job_data or {})
        missing = [key for key in required_keys if key not in job_description_dict or job_description_dict.get(key) in (None, False, "N/A", "")]
        if missing:
            logging.debug(f"Filling missing job_data keys with placeholders: {missing}")
        for k in missing:
            job_description_dict[k] = f"couldn't extract {k}"
        return job_description_dict
    
    def _construct_fallback_job(self, job_description_dict, parsed_date, e):
        # Catch pydantic ValidationError (or other) and attempt to construct
        # a best-effort Job by replacing invalid fields with safe placeholders.
        try:
            logging.warning(f"Job model validation failed: {e}")
            # Determine which fields failed if possible
            invalid_fields = set()
            if hasattr(e, 'errors'):
                for err in e.errors():
                    loc = err.get('loc')
                    if loc:
                        invalid_fields.add(loc[0])

            # Build fallback values
            def _fallback(field_name):
                if field_name in ('title', 'company', 'location', 'description'):
                    return f"couldn't extract {field_name}"
                return f"couldn't extract {field_name}"

            final_title = str(job_description_dict.get('title')) if 'title' not in invalid_fields else _fallback('title')
            final_company = str(job_description_dict.get('company')) if 'company' not in invalid_fields else _fallback('company')
            final_location = str(job_description_dict.get('location')) if 'location' not in invalid_fields else _fallback('location')
            final_description = (None if job_description_dict.get('description') in (None, False, "N/A", "") else str(job_description_dict.get('description')))
            if 'description' in invalid_fields:
                final_description = ''

            final_link = job_description_dict.get('url') if 'link' not in invalid_fields and 'url' not in invalid_fields else None
            final_posted = parsed_date if 'posted_date' not in invalid_fields else None

            # Last try to construct a Job with fallback values
            return Job(
                title=final_title,
                company=final_company,
                location=final_location,
                description=(None if final_description in (None, False, "N/A", "") else str(final_description)),
                link=final_link,
                posted_date=final_posted
            )
        except Exception as e2:
            logging.error(f"Failed to build fallback Job: {e2}", exc_info=True)
            return None

    def _calc_date_from_range(self, posted_date_str: str) -> datetime | None:
        """
        Convert a relative time string (e.g., '30d+', '1h') to a datetime object
        representing when the job was posted.
        """
        if not posted_date_str:
            return None
        
        try:
            return parse_time_expression(posted_date_str)
        except ValueError as e:
            logging.warning(f"Could not parse date string '{posted_date_str}': {e}")
            return None