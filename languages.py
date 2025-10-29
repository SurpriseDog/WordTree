#!/usr/bin/python3

import os
import sys
from letters import eprint

CACHE = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'cache')

eprint("Using cache folder:", CACHE)

LANGCODES = {'ar': 'Arabic', 'bg': 'Bulgarian', 'bn': 'Bengali', 'br': 'Breton', 'ca': 'Catalan', 'cs': 'Czech', 'da': 'Danish', 'de': 'German', 'el': 'Greek', 'en': 'English', 'eo': 'Esperanto', 'es': 'Spanish', 'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian', 'fi': 'Finnish', 'fr': 'French', 'gl': 'Galician', 'he': 'Hebrew', 'hi': 'Hindi', 'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian', 'it': 'Italian', 'ja': 'Japanese', 'ka': 'Georgian', 'kk': 'Kazakh', 'ko': 'Korean', 'lv': 'Latvian', 'mk': 'Macedonian', 'ml': 'Malayalam', 'nl': 'Dutch', 'no': 'Norwegian', 'pl': 'Polish', 'pt': 'Portuguese', 'pt-br': 'Brazilian', 'ro': 'Romanian', 'ru': 'Russian', 'sh': 'Serbo-Croatian', 'si': 'Sinhalese', 'sk': 'Slovak', 'sl': 'Slovene', 'sq': 'Albanian', 'sv': 'Swedish', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tl': 'Tagalog', 'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'vi': 'Vietnamese', 'zh': 'Chinese', 'pt-br' : 'Brazilian', 'zh-tw': 'Taiwanese'} # pylint: disable=line-too-long


# Spelling corrections
SPELLING = dict(\
	Albanain="Albanian",\
	Aribic="Arabic",\
	Armenain="Armenian",\
	Basc="Basque",\
	Bengali="Bengali",\
	Bretonn="Breton",\
	Brasilian="Brazilian",\
	Brazillian="Brazilian",\
	Brazilien="Brazilian",\
	Brasillian="Brazilian",\
	Bresilian="Brazilian",\
	Brazlian="Brazilian",\
	Brazilan="Brazilian",\
	Brasilain="Brazilian",\
	Bulgarain="Bulgarian",\
	Catalon="Catalan",\
	Chineese="Chinese",\
	Czeck="Czech",\
	Dansih="Danish",\
	Duth="Dutch",\
	Englsh="English",\
	Espernato="Esperanto",\
	Eestonian="Estonian",\
	Finsih="Finnish",\
	Franch="French",\
	Gallacian="Galician",\
	Georgain="Georgian",\
	Greman="German",\
	Greeek="Greek",\
	Hebru="Hebrew",\
	Hindhi="Hindi",\
	Hungarain="Hungarian",\
	Indonision="Indonesian",\
	Italien="Italian",\
	Japaneese="Japanese",\
	Kazack="Kazakh",\
	Koren="Korean",\
	Latvion="Latvian",\
	Macedonain="Macedonian",\
	Malyalam="Malayalam",\
	Mandarin="Chinese",\
	Mandrin="Chinese",\
	Norwiegian="Norwegian",\
	Persain="Persian",\
	Polnish="Polish",\
	Portugeese="Portuguese",\
	Roumanian="Romanian",\
	Rusian="Russian",\
	SerboCroation="Serbo-Croatian",\
	Sinhalaese="Sinhalese",\
	Slovack="Slovak",\
	Slovenean="Slovene",\
	Spannish="Spanish",\
	Sweedish="Swedish",\
	Tgalog="Tagalog",\
	Tammil="Tamil",\
	Telagu="Telugu",\
	Thia="Thai",\
	Turkesh="Turkish",\
	Ukranian="Ukrainian",\
	Urdoo="Urdu",\
	Veitnamese="Vietnamese",\
	Albenian="Albanian",\
	Aribian="Arabic",\
	Arminian="Armenian",\
	Basq="Basque",\
	Bangali="Bengali",\
	Bretton="Breton",\
	Bulgerian="Bulgarian",\
	Catelan="Catalan",\
	Chinnese="Chinese",\
	Check="Czech",\
	Dainsih="Danish",\
	Duch="Dutch",\
	Englesh="English",\
	Esparanto="Esperanto",\
	Estonian="Estonian",\
	Finesh="Finnish",\
	Frensh="French",\
	Galeecian="Galician",\
	Georgean="Georgian",\
	Germaan="German",\
	Griek="Greek",\
	Hebrow="Hebrew",\
	Hindie="Hindi",\
	Hungarian="Hungarian",\
	Indonessian="Indonesian",\
	Itallian="Italian",\
	Japaneze="Japanese",\
	Kazah="Kazakh",\
	Korian="Korean",\
	Latvian="Latvian",\
	Macedonian="Macedonian",\
	Malyayalam="Malayalam",\
	Norveigan="Norwegian",\
	Persian="Persian",\
	Polisch="Polish",\
	Portugues="Portuguese",\
	Rumainian="Romanian",\
	Russan="Russian",\
	SerboKroatian="Serbo-Croatian",\
	Sinhallese="Sinhalese",\
	Slovac="Slovak",\
	Slovinian="Slovene",\
	Slovenian="Slovene",\
	Spannisch="Spanish",\
	Sweadish="Swedish",\
	Taggalog="Tagalog",\
	Tamill="Tamil",\
	Telgugu="Telugu",\
	Thay="Thai",\
	Turqish="Turkish",\
	Ukrainien="Ukrainian",\
	Ordu="Urdu",\
	Vietnamse="Vietnamese",\
	Albenien="Albanian",\
	Arabik="Arabic",\
	Armanian="Armenian",\
	Basquee="Basque",\
	Bangalie="Bengali",\
	Bretan="Breton",\
	Bulgarin="Bulgarian",\
	Catalen="Catalan",\
	Chinees="Chinese",\
	Czechh="Czech",\
	Daneesh="Danish",\
	Duchh="Dutch",\
	Englisch="English",\
	Espranto="Esperanto",\
	Estonien="Estonian",\
	Finnisch="Finnish",\
	Frenche="French",\
	Galacian="Galician",\
	Georgien="Georgian",\
	Germon="German",\
	Grieck="Greek",\
	Hebreww="Hebrew",\
	Hindee="Hindi",\
	Hungeryan="Hungarian",\
	Indonesan="Indonesian",\
	Italin="Italian",\
	Japanise="Japanese",\
	Kazak="Kazakh",\
	Koryan="Korean",\
	Latvien="Latvian",\
	Macedonien="Macedonian",\
	Malaylam="Malayalam",\
	Norwagian="Norwegian",\
	Persion="Persian",\
	Pollish="Polish",\
	Portugese="Portuguese",\
	Romanien="Romanian",\
	Russion="Russian",\
	Sinhalesee="Sinhalese",\
	Slovackian="Slovak",\
	Slovane="Slovene",\
	Spanisch="Spanish",\
	Swedishh="Swedish",\
	Tagaloge="Tagalog",\
	Tamel="Tamil",\
	Teluugu="Telugu",\
	Tie="Thai",\
	Turckish="Turkish",\
	Ukraneian="Ukrainian",\
	Urduh="Urdu",\
	Veitnamse="Vietnamese",\
	Tw="Taiwanese",\
	)
	
SPELLING['Serbo-Croat'] = "Serbo-Croatian"


def fix_lang(lang):
	lang = lang.lower().strip()
	# eprint('debug fix_lang', lang)
	if not lang:
		eprint("Please enter a language. For example: --lang English")
		sys.exit(1)	
	
	
	if 'slovenian'in (lang):
		eprint("Wiktionary uses the language name: Slovene")

	if lang in ('bs', 'sr', 'hr'):
		eprint('''
		At last check, Wiktionary uses the code sh to refer to Serbo-Croatian languages.
		If you think this is a mistake, they have discussion pages here:
			https://en.wiktionary.org/wiki/Wiktionary:About_Serbo-Croatian
			https://en.wikipedia.org/wiki/Talk:Serbo-Croatian
		In the meantime, you can try using the following language code:
			--lang Serbo-Croatian --freq freq/sr.xz
		''')

		lang = guess_lang(lang)
		eprint("\nSet language to:", lang)
	return guess_lang(lang)
	
	
def guess_lang(code):
	"Look at language code or language name and attempt to guess the pair"

	# print('debug guess_lang', code)
	
	
	# Fix four digit lang codes
	if code.lower() == 'pt-br':
		return ['pt', 'Brazilian']
	if code.lower() == 'zh-tw':
		return ['zh', 'Taiwanese']

	langnames = {val: key for key, val in LANGCODES.items()}



	# First try looking for 2 digit code -> language
	code = code.lower().strip()
	if code in LANGCODES:
		return [code, LANGCODES[code]]

	lang = code.title()
	# Fix spelling
	if lang in SPELLING:
		lang = SPELLING[lang]
		
	# Look for corrected word in langnames
	if lang in langnames:
		return [langnames[lang], lang]
		
	# If it's not there try doing partial matches
	for name in langnames:
		if name.startswith(lang):
			eprint("Corrected", lang, 'to', name)
			return [langnames[name], name]

	eprint("Unknown language:", code)
	eprint("If this is a real language that's not in my list you can try typing --lang <code> <name>")
	eprint("For example: --lang en English")

	eprint("\nThese are the languages I know about:")
	eprint(' '.join(sorted(LANGCODES.values())))
	sys.exit(1)	
