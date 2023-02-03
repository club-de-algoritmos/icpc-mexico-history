import re
import time
from functools import wraps

_NORMALIZED_LETTERS = {
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'ñ': 'n',
}


def normalize_str(value: str) -> str:
    normalized_value = re.sub(' +', ' ', value.lower().strip())
    for letter, normalized_letter in _NORMALIZED_LETTERS.items():
        normalized_value = normalized_value.replace(letter, normalized_letter)
    return normalized_value


def normalize_as_filename(value: str) -> str:
    normalized_value = normalize_str(value).replace(' ', '-').replace('/', '-')
    normalized_value = re.sub('-+', '-', normalized_value)
    return normalized_value


def log_run_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'INFO: Function {func.__name__} took {total_time:.2f} seconds')
        return result
    return wrapper
