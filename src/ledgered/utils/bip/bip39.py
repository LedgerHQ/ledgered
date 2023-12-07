import random
from pathlib import Path
from typing import List, Union, Tuple

MNEMONIC_SIZES = [12, 18, 24]
FORMATS = [str, list, tuple]
FORMAT_TYPES = Union[str, List, Tuple]
DATA_PATH = Path(__file__).parent / 'data'
DATA_PREFIX = 'bip39_'


def generate_mnemonic(language: str = "english",
                      size: int = 24,
                      format: type = str) -> FORMAT_TYPES:
    """
    Generates a <size>-length mnemonic from the BIP39 word list of given <language>, outputted in
    <format>.

    :param language: The expected language from which words are selected
    :type language: str
    :param size: The expected mnemonic size (in [12, 18, 24])
    :type size: int
    :param format: The expected output format (in [str, list, tuple])
    :type format: type
    :return: The generated mnemonic
    :rtype: <format>
    """
    # various checks
    assert size in MNEMONIC_SIZES, \
        f"Incorrect mnemonic size '{size}', must be in these values: '{MNEMONIC_SIZES}'"
    assert format in FORMATS, \
        f"Incorrect mnemonic format '{format}', must be in these types: '{FORMATS}'"
    mnemonic_file = DATA_PATH / f"{DATA_PREFIX}{language}.txt"
    if not mnemonic_file.is_file():
        available_languages = list()
        for file_name in (f.name for f in DATA_PATH.iterdir() if f.name.startswith(DATA_PREFIX)):
            available_languages.append(file_name.removeprefix(DATA_PREFIX).removesuffix(".txt"))
        error_msg = (f"No mnemonic file found for language '{language}'. "
                     f"Available languages are: {available_languages}")
        raise ValueError(error_msg)
    # fetching all the possible words
    with mnemonic_file.open() as filee:
        mnemonic_words = [word.rstrip() for word in filee]
    # choosing according to expected size
    mnemonic_words = random.choices(mnemonic_words, k=size)
    # converting to expected type
    if format == str:
        return ' '.join(mnemonic_words)
    return format(mnemonic_words)
