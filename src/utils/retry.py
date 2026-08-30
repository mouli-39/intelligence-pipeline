import asyncio
import random
from typing import Callable, Any
from src.utils.logging import setup_logger

logger = setup_logger("retry_handler")

def with_retry(max_retries: int = 3, base_delay: float = 2.0, max_delay: float = 30.0):
    """Decorator applying exponential backoff with full jitter for transient issues and 429s."""
    def decorator(func: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Execution failed permanently after {max_retries} attempts.")
                        raise e
                    
                    # Full Jitter formula calculation
                    delay = min(max_delay, base_delay * (2 ** (retries - 1)))
                    jittered_delay = random.uniform(0.1, delay)
                    
                    logger.warning(
                        f"Transient failure detected: {str(e)}. "
                        f"Retrying attempt {retries}/{max_retries} in {jittered_delay:.2f} seconds."
                    )
                    await asyncio.sleep(jittered_delay)
        return wrapper
    return decorator
