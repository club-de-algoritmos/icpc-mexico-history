import re

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
