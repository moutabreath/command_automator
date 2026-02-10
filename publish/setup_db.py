import sys
from pymongo import MongoClient, ASCENDING
from app.api.setup.aplication_settings import application_settings


def create_database(): 

    connection_string = str(application_settings.mongo_uri)
    database_name = application_settings.mongo_db_name


    print(f"Connecting to MongoDB at {connection_string}...")
    client = MongoClient(connection_string)
    db = client[database_name]

    # 1. job_applications with indexes user_id, company_id
    print(f"Creating indexes for 'job_applications' in '{database_name}'...")
    job_applications = db['job_applications']
    # Creating a compound index for user_id and company_id
    job_applications.create_index([("user_id", ASCENDING), ("company_id", ASCENDING)])

    # 2. user with user_id as index
    print(f"Creating indexes for 'user' in '{database_name}'...")
    user_collection = db['user']
    user_collection.create_index([("user_id", ASCENDING)])

    print("Database initialization complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_database.py <path_to_config.json>")
    else:
        create_database(sys.argv[1])