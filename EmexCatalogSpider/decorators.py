import logging
import functools
import time


def retry(number_of_repeats):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(number_of_repeats):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logging.warning("{}: FUNCTION {}: Error occured: {}".format(time.asctime(), func, e.args))
                    if i == number_of_repeats - 1:
                        raise e
                    time.sleep(5)

        return wrapper

    return decorator
