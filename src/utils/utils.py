import asyncio
import logging


def run_async_method(async_method, *args, **kwargs):
    try:
        return asyncio.run(async_method(*args, **kwargs))
    except Exception as e:
        logging.error(f"Error running async method {e}", exc_info=True)
        return None # Called should know if it should recieve None