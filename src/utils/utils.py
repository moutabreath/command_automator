import asyncio
import threading
import logging
from typing import TypeVar, Any, Coroutine, Optional, Callable

def run_async_method(async_method, *args, **kwargs):
    try:
        return asyncio.run(async_method(*args, **kwargs))
    except Exception as e:
        logging.error(f"Error running async method {e}", exc_info=True)
        return None # Caller must handle None return


T = TypeVar('T')

class AsyncRunner:
    """
    Manages a background asyncio event loop running in a separate thread.
    Allows synchronous code (like pywebview API methods) to execute 
    coroutines on that background loop thread-safely.
    """
    
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _loop_thread: Optional[threading.Thread] = None
    _started = False

    @classmethod
    def start(cls):
        """
        Starts the persistent event loop in a daemon thread.
        This must be called BEFORE webview.start().
        """
        if cls._started:
            return

        def _start_background_loop(loop: asyncio.AbstractEventLoop):
            asyncio.set_event_loop(loop)
            try:
                loop.run_forever()
            finally:
                # Clean up generators, etc.
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                except Exception as e:
                    logging.error(f"Error closing loop: {e}")

        cls._loop = asyncio.new_event_loop()
        cls._loop_thread = threading.Thread(
            target=_start_background_loop, 
            args=(cls._loop,), 
            daemon=True,
            name="AsyncBackgroundLoop"
        )
        cls._loop_thread.start()
        cls._started = True
        logging.info("AsyncRunner: Background event loop started.")

    @classmethod
    def get_loop(cls) -> asyncio.AbstractEventLoop:
        """Returns the running background loop."""
        if not cls._loop:
            raise RuntimeError("AsyncRunner not initialized. Call AsyncRunner.start() first.")
        return cls._loop

    @classmethod
    def run_async(cls, coro: Coroutine[Any, Any, T]) -> T:
        """
        Thread-safe execution of a coroutine from a synchronous context.
        
        This submits the coroutine to the background loop and blocks 
        the calling thread until the result is ready.
        """
        if not cls._loop:
            raise RuntimeError("AsyncRunner.start() must be called before running async tasks.")

        # This is the magic bridge:
        # It schedules the coroutine on the background loop safely.
        future = asyncio.run_coroutine_threadsafe(coro, cls._loop)
        
        try:
            # Block this thread (the UI thread) until result is ready
            return future.result()
        except Exception as e:
            logging.error(f"AsyncRunner Error: {e}")
            raise e

    @classmethod
    def shutdown(cls):
        """Stops the background loop gracefully."""
        if cls._loop and cls._loop.is_running():
            logging.info("AsyncRunner: Stopping background loop...")
            cls._loop.call_soon_threadsafe(cls._loop.stop)
            
        if cls._loop_thread:
            cls._loop_thread.join(timeout=2.0)