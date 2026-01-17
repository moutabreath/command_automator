import logging, os, sys
from dotenv import load_dotenv

import webview, sys, logging

from jobs_tracking.job_tracking_api import JobTrackingApi
from jobs_tracking.services.job_tracking_service import JobTrackingService

from llm.llm_api import LLMApi
from llm.services.llm_service import LLMService

from scripts_manager.scripts_manager_api import ScriptsManagerApi

from user.services.user_registry_service import UserRegistryService
from user.user_api import UserApi

from utils.logger_config import setup_logging


from commands_automator_api import CommandsAutomatorApi

from utils.utils import AsyncRunner
from utils.logger_config import setup_logging


def load_environment():
    """Load environment variables from .env.local file"""
    try:
        # Try to load .env.local from current directory first (development)
        if os.path.exists('.env.local'):
            load_dotenv('.env.local')
        # For PyInstaller, try loading from the executable's directory
        elif hasattr(sys, '_MEIPASS'):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            env_path = os.path.join(os.path.dirname(sys.executable), '.env.local')
            if os.path.exists(env_path):
                load_dotenv(env_path)
        # Try APPDATA directory as fallback
        else:
            appdata_env = os.path.join(os.getenv('APPDATA', ''), 'commands_automator', '.env.local')
            if os.path.exists(appdata_env):
                load_dotenv(appdata_env)
    except Exception as e:
        logging.warning(f"Could not load .env.local file: {e}")


async def initialize_apis():
    """Initialize all APIs"""

    scripts_manager_api = ScriptsManagerApi()
    
    llm_service = LLMService()
    llm_service.run_mcp_server()
    llm_api = LLMApi(llm_service)

    user_api = None
    job_tracking_api = None

    load_environment()
    
    mongo_connection_string = os.getenv('MONGODB_URI')
    db_name = os.getenv('MONGODB_DB_NAME')
    
    if not db_name or not mongo_connection_string:
        logging.warning("MongoDB configuration not found in .env.local. Database-related features will be disabled.")
    else:
        try:
            user_registry_service = await UserRegistryService.create(mongo_connection_string=mongo_connection_string, db_name=db_name)
            user_api = UserApi(user_registry_service)

            job_tracking_service = await JobTrackingService.create(mongo_connection_string=mongo_connection_string, db_name=db_name)
            job_tracking_api = JobTrackingApi(job_tracking_service)
        except Exception as e:
            logging.error(f"Error initializing database APIs: {e}")

    return scripts_manager_api, llm_api, user_api, job_tracking_api



def main():
    try:
        setup_logging()  # Set up logging at the application entry point
        logging.info("Starting Commands Automator application...")

        AsyncRunner.start()
        
        scripts_manager_api, llm_api, user_api, job_tracking_api = AsyncRunner.run_async(initialize_apis())
        # Initialize API and create window
        api = CommandsAutomatorApi(scripts_manager_api, llm_api, user_api, job_tracking_api)
        window = webview.create_window(
            'Commands Automator',
            'ui/commands_automator.html',
            js_api=api,
            width=1500,
            height=1000
        )
        
        logging.info("Starting webview...")
        webview.start(icon='ui/resources/Commands_Automator.ico')
    except Exception as ex:
        logging.exception(f"Fatal error in main: {ex}")
        raise

if __name__ == '__main__':
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    main()