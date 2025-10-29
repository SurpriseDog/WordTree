#!/usr/bin/python3

import sys
import string

try:
	from unidecode import unidecode
except ModuleNotFoundError:
	print("Could not load unidecode module. Spelling correction will be limited.")
	print("\tTo install unidecode, please run: python3 -m pip install unidecode")
	print("\tand then delete spelling.json inside the cache folder.\n\n")


# Punctuation table
def gen_punct():
	punct = str.maketrans(dict.fromkeys(string.punctuation))
	for letter in "—¡¿«»0123456789…“”–":
		punct[ord(letter)] = None
	return punct


def eprint(*args, **kargs):
	print(*args, file=sys.stderr, **kargs)


def strip_punct(word):
	"Strip punctuation and normalize word. Does not auto lower words!"
	return word.strip().translate(PUNCT)


def make_unidecode(src, verbose=False):
	"Make unidecode backup of common letters"

	common = src.strip().replace(' ', '').replace('-', '')

	translations = dict()
	for letter in common:
		if letter not in translations:
			t = unidecode(letter)
			if t != letter:
				translations[letter] = t
	if verbose:
		eprint('TRANSLATIONS =', translations, "# pylint: disable = line-too-long")


def make_spellings(words):
	"Make a dict of all words without accents"
	miss = dict()			# dict of misspelled words -> accented orignal

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




# Globals:
PUNCT = gen_punct()


COMMON_SYMBOLS = "á é í ó ú - ã ñ õ - à è ì ò ù - ä ë ï ö ü ÿ - â ê î ô û - č š ž - ą ę ł ż - å æ ç œ ı ø ß"
	# Chat search: 	Accented Character Checklist
	# č š ž			(common in Czech, Slovak, Slovene, Croatian)
	# ą ę ł ż		Polish, Lithuanian
	# â ê î ô û		Circumflex letters - Frenche
	# ä ë ï ö ü ÿ 	Umlauts (diaeresis) 


# Translations is included explicity in case the user can't run unidecode
# Run ./letters.py to regenerate
TRANSLATIONS = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ã': 'a', 'ñ': 'n', 'õ': 'o', 'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u', 'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u', 'ÿ': 'y', 'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u', 'č': 'c', 'š': 's', 'ž': 'z', 'ą': 'a', 'ę': 'e', 'ł': 'l', 'ż': 'z', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'œ': 'oe', 'ı': 'i', 'ø': 'o', 'ß': 'ss', 'ů': 'u', 'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u', 'į': 'i', 'ų': 'u', 'þ': 'th', 'İ': 'I', 'ð': 'd'} # pylint: disable = line-too-long



def gen_translations():
	src = COMMON_SYMBOLS + " ů ā ē ī ō ū ą ę į ų þ İ į ų ð"
	print("Processing:", src)
	make_unidecode(src, verbose = True)


if __name__ == "__main__":
	print('PUNCT =', gen_punct())
	gen_translations()


	
