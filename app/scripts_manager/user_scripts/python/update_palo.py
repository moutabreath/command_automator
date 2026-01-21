import uuid
import pymongo
from bson.objectid import ObjectId
from datetime import datetime

# Connection setup
# Update the URI and DB name as needed for your Atlas cluster
client = pymongo.MongoClient("mongodb://localhost:27017/") 
db = client["job_tracker"] 
collection = db["job_applications"]

# Constants
# Corrected 24-character hex string from Atlas
TARGET_ID = ObjectId('695ccdfaa92f6ec1f668f236')
USER_ID = "59555ad1-42c2-44d4-84e0-01c9fa741ec3"
COMPANY_ID = "608ad442-1d3c-4a2b-abd4-ec08b340c4da"
CONTACT_NAME = "Eliah Ninyo"
CONTACT_LINKEDIN = "https://www.linkedin.com/in/eliahninyo/"
NOW = datetime.now()

# Raw job data
job_list_raw = [
    ("Senior Java Engineer Software (Cortex Cloud)", "47263/90105295232"),
    ("Senior Engineer Software - Identity Security (Cortex Cloud)", "47263/90147057872"),
    ("Senior Software Engineer - (Cortex Content)", "47263/90239424416"),
    ("Senior Java Backend Engineer (Cortex Cloud)", "47263/89759721520"),
    ("Sr Backend Engineer Application team - ASPM (Cortex Cloud)", "47263/89618050272"),
    ("Experienced Java Software Engineer (Cortex Cloud)", "47263/89267151168"),
    ("Senior AI Engineer, Security Research & Automation (Cortex)", "47263/89086616880"),
    ("Senior Software Engineer-Platform Backend (Cortex)", "47263/87520837312"),
    ("Senior Backend Engineer Software (Cortex XSIAM & Platform)", "47263/84287479824"),
    ("Senior Full Stack Engineer (Prisma Browser)", "47263/82828985280"),
    ("Senior Software Engineer Broker Team (Cortex)", "47263/81414071616"),
    ("Sr Backend Engineer (Prisma Browser)", "47263/81184260256"),
]

# Map to the job object structure
jobs_to_push = [
    {
        "job_title": title,
        "job_url": f"https://jobs.paloaltonetworks.com/en/job/tel-aviv/{path}",
        "applied_date": NOW,
        "job_state": "MESSAGE_SENT",
        "contact_name": CONTACT_NAME,
        "contact_linkedin": CONTACT_LINKEDIN
    }
    for title, path in job_list_raw
]

# Update operation
try:
    result = collection.update_one(
        {
            "_id": TARGET_ID,
            "user_id": USER_ID,
            "company_id": COMPANY_ID
        },
        {"$push": {"jobs": {"$each": jobs_to_push}}}
    )
    
    if result.matched_count > 0:
        print(f"Success! Matched document. Modified: {result.modified_count}")
        print(f"Added {len(jobs_to_push)} jobs to the application list.")
    else:
        print("FAILED: No document found.")
        # Final diagnostic check
        exists_by_id = collection.find_one({"_id": TARGET_ID})
        if not exists_by_id:
            print(f"The _id {TARGET_ID} definitely does not exist in this collection.")
        else:
            print("The _id exists, but user_id or company_id do not match.")

except Exception as e:
    print(f"An error occurred: {e}")


def backfill_job_ids():
    # 1. Find the document to get the current jobs
    doc = collection.find_one({
        "_id": TARGET_ID,
        "user_id": USER_ID,
        "company_id": COMPANY_ID
    })

    if not doc:
        print("Document not found.")
        return

    jobs = doc.get("jobs", [])
    updated_count = 0

    # 2. Iterate and update only those missing job_id
    # We use update_one with arrayFilters for precision
    for index, job in enumerate(jobs):
        if "job_id" not in job:
            new_job_id = str(uuid.uuid4())
            
            # Update the specific array element by its index
            collection.update_one(
                {"_id": TARGET_ID},
                {"$set": {f"jobs.{index}.job_id": new_job_id}}
            )
            updated_count += 1

    print(f"Backfill complete. Added job_id to {updated_count} jobs.")

def add_new_job():
    new_job = {
    "job_id": str(uuid.uuid4()),  # Generates a unique ID for this specific job
    "job_title": "Principal Software Engineer- KSPM (Cortex Cloud)",
    "job_url": "https://jobs.paloaltonetworks.com/en/job/tel-aviv/principal-software-engineer-kspm-cortex-cloud/47263/82828985280", # Path completed based on standard format
    "applied_date": datetime.fromisoformat("2026-01-14T14:14:40.201+00:00"),
    "job_state": "MESSAGE_SENT",
    "contact_name": "Eliah Ninyo",
    "contact_linkedin": "https://www.linkedin.com/in/eliahninyo/",
    "contact_email": None
    }

    # Execute the update
    try:
        result = collection.update_one(
            {
                "_id": TARGET_ID,
                "user_id": USER_ID,
                "company_id": COMPANY_ID
            },
            {"$push": {"jobs": new_job}}
        )
        
        if result.matched_count > 0:
            print(f"Successfully added Principal Software Engineer role.")
            print(f"Generated Job ID: {new_job['job_id']}")
        else:
            print("Document not found. Please check your _id, user_id, and company_id.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    add_new_job()