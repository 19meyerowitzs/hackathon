import time
from functools import wraps


def exponential_backoff_decorator(max_retries: int, base_delay: float, message: str = ""):
    """
    gradually increases the time between consecutive retry attempts, allowing the system more time to recover
    :param max_retries: maximum number of retries
    :param base_delay: initial delay in seconds that increase
    :param message: Specific function-wise error message
    :return:
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            Error = None
            while retries < max_retries:
                try:
                    result_func = func(*args, **kwargs)
                    return result_func
                except Exception as e:
                    error_message = f"Attempt {retries + 1} failed: error '{e}' in '{str(func)}' -- more details '{message}'"
                    # Check if exception has a response and print response text if available
                    if hasattr(e, 'response') and e.response is not None:
                        try:
                            error_message += f"\nResponse '{e.response}' with text: '{e.response.text}'"
                        except Exception as response_error:
                            error_message += f"\nCould not retrieve response text: '{response_error}'"
                    print(error_message)
                    delay = (base_delay * (2**retries))
                    retries += 1
                    Error = e
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
            raise Exception(f"{func.__name__} Max retries reached, operation failed. Error: {Error}")

        return wrapper

    return decorator
