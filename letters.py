#!/usr/bin/python3

import sys
import string

try:
    from unidecode import unidecode
except ModuleNotFoundError:
    print("Could not load unidecode module. Spelling correction will be limited.")
    print("\tTo install unidecode, please run: python3 -m pip install unidecode")
    print("\tand then delete spelling.json inside the 'cache' folder.\n\n")


COMMON_SYMBOLS = "á é í ó ú - ã ñ õ - à è ì ò ù - ä ë ï ö ü ÿ - â ê î ô û - å æ ç ð œ ø ß"

# output of make_unidecode:
TRANSLATIONS = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ã': 'a', 'ñ': 'n', 'õ': 'o', 'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u', 'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u', 'ÿ': 'y', 'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'ð': 'd', 'œ': 'oe', 'ø': 'o', 'ß': 'ss'} # pylint: disable=line-too-long


# Punctuation table
def gen_punct():
    punct = str.maketrans(dict.fromkeys(string.punctuation))
    for letter in "—¡¿«»123456789…":
        punct[ord(letter)] = None
    return punct

PUNCT = gen_punct()

def eprint(*args, **kargs):
    print(*args, file=sys.stderr, **kargs)


def strip_punct(word):
    "Strip punctuation and normalize word"
    return word.lower().strip().translate(PUNCT)


def make_unidecode():
    "Make unidecode backup of common letters"

    common = COMMON_SYMBOLS.strip().replace(' ', '').replace('-', '')

    translations = dict()
    for letter in common:
        t = unidecode(letter)
        if t != letter:
            translations[letter] = t
    eprint('TRANSLATIONS =', translations)


def make_spellings(words):
    "Make a dict of all words without accents"
    miss = dict()           # dict of misspelled words -> accented orignal

    def simple_decode(word):
        out = list()
        for c in word:
            if c in TRANSLATIONS:
                out += TRANSLATIONS[c]
            else:
                out += c
        return ''.join(out)

    if 'unidecode' not in sys.modules:
        print("Attempting spelling corrections with limited table.")
        decode = simple_decode
    else:
        decode = unidecode

    for word in words:
        basic = decode(word)
        if basic != word:
            if basic not in miss:
                miss[basic] = []
            miss[basic].append(word)
    return miss


if __name__ == "__main__":
    print('PUNCT =', gen_punct())
    make_unidecode()
