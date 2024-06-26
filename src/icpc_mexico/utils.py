import re
import time
from functools import wraps
from typing import List

_NORMALIZED_LETTERS = {
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'ñ': 'n',
    'ü': 'u',
}


def normalize_str(value: str) -> str:
    normalized_value = re.sub(' +', ' ', value.lower().strip())
    for letter, normalized_letter in _NORMALIZED_LETTERS.items():
        normalized_value = normalized_value.replace(letter, normalized_letter)
    return normalized_value.replace('"', '')


def normalize_school_name(value: str) -> str:
    return normalize_str(value).replace('technologico', 'tecnologico')


def normalize_as_filename(value: str) -> str:
    normalized_value = normalize_str(value).replace(' ', '-').replace('/', '-')
    return re.sub('-+', '-', normalized_value)


def contains_strings(string: str, *args: str) -> bool:
    for substring in args:
        if substring in string:
            return True
    return False


def get_percentile(rank: int, count: int) -> float:
    return (count - rank) / float(count - 1)


def format_percentile(percentile: float) -> str:
    return f'{round(percentile * 100)}%'


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
