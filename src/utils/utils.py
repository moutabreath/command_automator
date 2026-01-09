import asyncio
import threading
import logging
from typing import TypeVar, Any, Coroutine, Optional, Callable, Set



T = TypeVar('T')

_active_tasks: Set[asyncio.Task] = set()
_task_lock = threading.Lock()
_current_llm_task: Optional[asyncio.Task] = None
_llm_task_lock = threading.Lock()

def cancel_current_async_operation():
    """Cancel all currently running async operations"""
    global _active_tasks, _current_llm_task    
    with _llm_task_lock:
        if _current_llm_task and not _current_llm_task.done():
            _current_llm_task.cancel()
            logging.debug("Cancelled current LLM task")
            _current_llm_task = None

def set_current_llm_task(task: asyncio.Task):
    """Set the current LLM task for tracking"""
    global _current_llm_task
    with _llm_task_lock:
        _current_llm_task = task

def clear_current_llm_task():
    """Clear the current LLM task"""
    global _current_llm_task
    with _llm_task_lock:
        _current_llm_task = None

def run_async_method(async_method: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs) ->  Optional[T]:
    """
     Runs an async method synchronously. Returns None on error after logging.
    """
    global _active_tasks, _current_llm_task
    try:
        async def _wrapped_method():
            return await async_method(*args, **kwargs)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            task = loop.create_task(_wrapped_method())
            with _task_lock:
                _active_tasks.add(task)
            
            # If this looks like an LLM task, track it separately
            if hasattr(async_method, '__name__') and 'llm' in async_method.__name__.lower():
                set_current_llm_task(task)
            
            try:
                result = loop.run_until_complete(task)
                clear_current_llm_task()
                return result
            finally:
                with _task_lock:
                    _active_tasks.discard(task)
                clear_current_llm_task()
        finally:
            loop.close()
    except asyncio.CancelledError:
        logging.debug("Async operation was cancelled")
        clear_current_llm_task()
        raise
    except Exception as e:
        logging.error(f"Error running async method {e}", exc_info=True)
        clear_current_llm_task()
        return None # Caller must handle None return


class AsyncRunner:
    """
    Manages a background asyncio event loop running in a separate thread.
    Allows synchronous code (like pywebview API methods) to execute 
    coroutines on that background loop thread-safely.
    """
    
    _lock = threading.Lock()
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _loop_thread: Optional[threading.Thread] = None
    _started = False

    @classmethod
    def start(cls):
        """
        Starts the persistent event loop in a daemon thread.
        This must be called BEFORE webview.start().
        """
        with cls._lock:
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
        if not cls._started or not cls._loop:
            raise RuntimeError("AsyncRunner not initialized. Call AsyncRunner.start() first.")
        if not cls._loop.is_running():
            raise RuntimeError("AsyncRunner loop is not running.")
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
            return future.result(timeout=30.0)  # Adjust timeout as needed
        except Exception as e:
            logging.error(f"AsyncRunner Error: {e}")
            raise

        
    @classmethod
    def shutdown(cls):
        """Stops the background loop gracefully."""
        if cls._loop and cls._loop.is_running():
             logging.info("AsyncRunner: Stopping background loop...")
             cls._loop.call_soon_threadsafe(cls._loop.stop)
             
        if cls._loop_thread:
             cls._loop_thread.join(timeout=2.0)
             if cls._loop_thread.is_alive():
                logging.warning("AsyncRunner: Background thread did not terminate within timeout.")
        
            # Reset state to allow restart
        with cls._lock:
            cls._loop = None
            cls._loop_thread = None
            cls._started = False
        logging.info("AsyncRunner: Shutdown complete.")
