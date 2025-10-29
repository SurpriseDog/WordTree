#!/usr/bin/python3


import os
import sys
import csv
import platform


from letters import eprint
from sd.easy_args import ArgMaster
from languages import fix_lang, CACHE



def process_rae():
	'''
	Extracts frequency data from the file at https://www.rae.es/banco-de-datos/corpes-xxi
	This data is in tsv form (tab separated)
	Column D is the word and Column F is the number of hits
	'''
	
	filepath = ""	# File path of rae file
	for filepath in os.listdir('.'):
		if filepath.startswith('diccionario_frecuencias') and filepath.endswith('tsv'):
			break
	else:
		eprint('''
		Please download the frequency data file from:
		https://www.rae.es/banco-de-datos/corpes-xxi
		
		Direct link:
		https://www.rae.es/corpes/assets/rae/files/corpes/diccionario_frecuencias_corpes_alfa.tsv
		
		and save it in the Wordtree folder.	
		'''
		)		
		sys.exit(1)
	
	oname = os.path.join(CACHE, 'rae.txt')
	data = dict()
	eprint("Processing data from", filepath, "to", oname)	
	
	
	with open(oname, 'w', encoding='utf-8') as output:
		with open(filepath, 'r', encoding='utf-8') as file:
			reader = csv.reader(file, delimiter='\t')
			next(reader)  # Skip header row

			for row in reader:
				if len(row) >= 6:
					forma = row[3].strip()
					try:
						freq = int(row[5])
					except ValueError:
						continue  # Skip rows where frequency isn't a valid integer
						
					forma = forma.lower()
					
					if not forma:
						continue
					if ' ' in forma:
						continue
					if '\xa0' in forma:
						continue
						
					# RAE is double counting captalized words
					if forma in data:
						data[forma] = data[forma] + freq
					else:
						data[forma] = freq	

		for forma, freq in sorted(data.items(), key=lambda item: item[1], reverse=True):
			# print(forma, freq)
			output.write(forma + '\t' + str(freq) + '\n')


def parse_args():
	"Parse arguments"

	positionals = [\
	["filename", '', str],
	'''.txt, .csv or kindle My Clippings.txt file to read list of words from.
	Put a # before any lines you want to ignore.
	Right now only single words are supported.
	If multiple words are given on a line only the first word will be processed unless the file is My Clippings.txt'''
	]

	language = [\
	['lang', '', str],
	'''Language name
	For example: --lang es or --lang Spanish will show you Spanish words.
	''',
	]
	
	'''
	# Todo if the 2 digits codes are needed again just do a --langcode
		# The whole --lang es Spanish vs --lang es --lang Spanish was just confusing
	
	For more control, you can type the full set of language code + name like this:
	--lang <2 digit code> <language name>
	If you are typing the full set, then the language code and name must EXACTLY match the words used in Wiktionary or it won't detect the entries. For example, --lang sk Slovak will give you the Slovak language, but --lang sk Slovakian won't find anything. Go to https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to look up your language code and name.
	'''

	frequencies = [\
	['book', '', str],
	'''Location of a book file to use for additional frequency information.
	Must be in .txt format, NOT an e-reader format like .mobi - You can convert books to .txt format using the open-source Calibre program.
	The more a word appears in the boot, the more it will receive a boost in the adjusted frequency rankings.''',
	['freq', '', str, ''],
	'''Change the location of the default frequency list. (Must match language with --lang)
	This is useful for specifying the Taiwanese or Brazilian version of the language.
	''',
	['rae', '', bool, False],
	"Use frequency list from the RAE corpus. (Requires download)",
	['wikifreq', '', bool, False],
	'''Use frequency lists gathered from Wikipedia instead of subtitles. This is useful if you want to focus more on the written word instead of the spoken word. However, Wikipedia covers academic topics more than you may see in real life depending on what books you read. For example: yacimiento (Mineral Deposit) comes in at 0.87 fpm, but in Wikipedia it's at a staggering 34 fpm.''',
	]


	input_list = [\
	['rankbook', '', str],
	"Rank all the words in a book by number of occurences and analyze them. Must be in .txt format.",
	['ignore', '', str],
	"Ignore words on this list.\nEach word on the ignore list cancels out one word on the word list.",
	"Debugging mode.",
	['wikiroots', '', bool, False],
	"Why supply your own word list when you can rank every single root word in the dictionary?",
	['wikiwords', '', bool, False],
	"Show every word in the dictionary.\n(This will take awhile unless you combine it with --csv)",
	['skiplines', '', int, 0],
	"Skip lines at start of words list. (Helpful if you want to resume a session later)",
	['dupes', '', str, ''],
	"Manual input mode: check inputed words against a file and look for duplicates ",
	['multiline', '', str, 'autodetect'],
	'''
	True = Read one word per line. (A vertical list)
	False = Read multiple words per line (A book)
	'''
	]

	display = [\
	['csv', '', str],
	"Output data as csv filename instead of displaying. Example: --csv output.csv",
	['noentry', '', bool, False],
	'''Don't display the Wiktionary entry for each word (radically increases processing speed)''',
	['wikiclean', '', int, 1],
	"Attempt to cleanup the Wiktionary entry instead of showing raw wikicode. 0 = disable.",
	['showall', '', bool, False],
	"Show all conjugations instead of hiding the extremely uncommon ones.",
	['bookfpm', '', bool, False],
	"Show the book fpm in addition to the counts. (The longer the book, the more accurate this will be)",
	['stars', '', bool, False],
	"Include abnormally high star words in the total when sorting or displaying",
	['starval', '', int, 5],
	"Ratio of a conjugated word's fpm to the baseline to mark it with a star.",	
	]
	
	filtering = [\
	['min', '', float, 0],
	"Minimum total fpm to show a word candidate (not adjusted)",
	['max', '',	float, 0],
	"Maximum total fpm to show a word. (useful for filtering out super common words like: the)",
	['length', '', int, 2],
	"Skip words under given length.",
	['start', '', float, 0],
	"Start the ranked list at this word number.",
	['stop', '', float, 0],
	'''
	Stop the ranked list at this word number. 
	Example: --wikiroots --stop 10e3 will give you the top 10,000 Wikiroots.
	''',
	]


	sorting = [\
	['reverse', '', bool],
	"Reverse the word list",
	['nosort', '', bool],
	'''
	Turn off sorting. 
	Otherwise it will loosely sort the words from highest fpm to lowest
	applying a formula based on the original word's fpm and it's total derived fpm.
	''',
	['bookfactor', '', int, 50],
	'''
	How much the book fpm affect adjustment ranking.''',
	['dupefactor', '', int, 50],
	'''
	Rank duplicate words in a list higher.
	''',
	['sortfactor', '', int, 0],
	'''
	How much the source word fpm influence the sorting vs the total fpm.
	''',
	]	
	# All factors are out of 100 percent, but are left unbounded.
	# They apply a weighted bias toward the weighted_log_avg function. 
	# Using the weighted logarithmic average works best for fpms.
	# For example, a factor of 10 applies a weight of 0.1 for the original word
	# Factors can be negative which just applies the weight toward the other number
	

	anki = [\
	['anki', '', str, 'USER_DID_NOT_INPUT'],
	'''
	Leave blank to auto-determine you anki location.
	Location of your colection.anki2 or .apkg file to check to see if the search word already has a note.
	Only searches the first few words of the front card to avoid any example sentences.
	If you get a 'Database is Locked' error, then you need to close Anki first or simply export the cards you wish to search to a .apkg file (recommended)
	''',
	['skipanki', '', bool],
	"Skip any cards that are already in anki database instead of just noting them.",
	['decks', '', list],
	'''Which anki decks to pull cards from.
	For example if you have subdecks named words and examples under the deck A
	then type --decks A::words A::examples
	''',
	['ankilimit', '', int, 9],
	"Number of words to search in the anki question field.",
	]


	# debug level 3 will rebuild caches
	hidden = [\
	['debug', '', int, 0],
	]

	am = ArgMaster(\
		usage='<txt/csv word list>, --options...',
		description="Scan Wiktionary to determine a word's root and frequency of conjugations in fpm (Frequency per million words)")
	am.update(language, title="\nLanguage:")
	am.update(input_list, title="\nInput word list:")
	am.update(filtering, title="\nFiltering the list.")
	am.update(sorting, title="\nSorting the list:")
	am.update(display, title="\nDisplay options:")
	am.update(frequencies, title="\nFrequency lists:")
	am.update(anki, title="\nConnect with Anki")
	am.update(positionals, title="Positional Arguments", positionals=True, hidden=True)
	am.update(hidden, "Used for testing purposes:", hidden=True)
	args = am.parse()

	# Language codes
	# if '-lang' not in ' '.join(sys.argv[:]).lower():
	if not args.lang:
		eprint("Use --lang to set a language\n")
		eprint("For example: wordtree.py --lang English")
		sys.exit(1)

	args.lang = fix_lang(args.lang)

	# args.multiline
	choice = args.multiline.lower().strip()[:1]
	if choice == 'a':
		args.multiline = -1
	elif choice in 't1':
		args.multiline = 1
	elif choice in 'f0':
		args.multiline = 0
	else:
		eprint("Unknown args.multiline parameter")
		sys.exit(1)


	def apath(path):
		if not path or not path.strip():
			return path
		path = os.path.abspath(path)
		return path


	# Guess anki location
	# args.skipanki implies args.anki
	if args.skipanki:
		args.anki = ""
		
		
	args.anki = guess_anki(args.anki)
	# print('debug anki', args.anki)

	# Fix paths		
	args.filename = apath(args.filename)
	args.book = apath(args.book)
	args.freq = apath(args.freq)
	args.rankbook = apath(args.rankbook)
	args.ignore = apath(args.ignore)
	args.dupes = apath(args.dupes)
	args.csv = apath(args.csv)


	# Verify arguments are correct
	if not check_args(args):
		sys.exit(1)

	return args


def check_args(args):
	# Checking
	status = False
	if args.filename and not os.path.exists(args.filename):
		eprint("Can't find file named:", args.filename)
	elif args.anki and os.path.splitext(args.anki)[-1] not in ('.anki2', '.apkg'):
		eprint("Unexpected filename extension for --anki:", args.anki)
		eprint("These files should end in .apkg or .anki2")		
	elif args.dupes and not os.path.exists(args.dupes):
		eprint("Can't find file named:", args.dupes)
	elif args.freq and not os.path.exists(args.freq):
		eprint("Can't find file:", args.freq)
	elif args.csv and not args.csv.endswith('.csv'):
		eprint("csv output file must end with .csv to prevent accidentally overwriting the wrong file.")
	else:
		status = True
	if not status:
		return False

	if not args.freq:
		args.freq = choose_freq(args)
		eprint("\nUsing frequency file:", args.freq)
	if not os.path.exists(args.freq):
		eprint("No frequency file found for language:", args.lang[0], 'at', args.freq)
		return False
		
		
	# Corrections to match wiki format	
	if args.lang[1] == 'Brazilian':
		eprint("Note: Wiktionary doesn't separate out Brazilian Portuguese, but the OpenSubtitles frequency list does.")
		args.lang = ['pt', 'Portuguese']
	if args.lang[1] == 'Taiwanese':
		eprint("Note: Wiktionary doesn't separate out Taiwanese Mandarin, but the OpenSubtitles frequency list does.")
		args.lang = ['zh', 'Chinese']	

	eprint("Language code:", args.lang)	
	return True
	
	
	
def choose_freq(args):
	# Determine frequency file if not given		
	if args.wikifreq:
		return os.path.join('wikifreq', args.lang[0] + '.xz')
	elif args.rae:
		freq = os.path.join(CACHE, 'rae.txt')
		if not os.path.exists(freq):
			process_rae()
		return freq	
					
	else:
		code = args.lang[0]
		lang = args.lang[1]
		
		print('debug choose_freq', 'code', code, 'lang', lang)
		
		# Corrections for subset languages
		if lang == 'Brazilian':
			return os.path.join('freq', 'pt_brazilian.xz')
		if lang == 'Taiwanese':
			return os.path.join('freq', 'zh_taiwan.xz')
							
							
		if code == 'pt':
			eprint("\nWarning: Using Portugal Portuguese not Brazilian Portuguese which has some different words.")
			eprint("Try --lang Brazil or --lang Brazilian if that's what you wish to learn.\n")
		elif code == 'zh':
			eprint("\nWarning Using Mandarin Chinese (Simplified).")
			eprint("To use the Taiwanese Mandarin database, type --lang Taiwanese.\n")
		elif code == 'sh':
			code = 'sr'
			eprint("Defaulting to serbian frequency file.")
		return os.path.join('freq', code + '.xz')
	

			

def guess_anki(path):
	if path and path.endswith('USER_DID_NOT_INPUT'):
		return None
	if path:
		return path		# user defined location

	if platform.system() == 'Windows':
		path = os.path.join(os.getenv('APPDATA'), 'Anki2')
	elif platform.system() == 'Linux':
		path = "~/.local/share/Anki2"
	elif platform.system() == 'Darwin':
		path = "~/Library/Application Support/Anki2"
	else:
		eprint("Unexpected system platform", platform.system())
		eprint("Please enter the .anki2 location manually using --anki <location>")
		sys.exit(1)
	path = os.path.expanduser(path)
	if not os.path.exists(path):
		eprint("Could not find directory:", path)
		eprint("Please enter the .anki2 location manually using --anki <location>")
		sys.exit(1)
	path = os.path.join(path, 'User 1/collection.anki2')
	if not os.path.exists(path):
		eprint("Could not find .anki2 file :", path)
		eprint("Please enter the .anki2 location manually using --anki <location>")
		sys.exit(1)
	eprint("Using default anki location:", path)
	return path



def tester():
	os.chdir(sys.path[0])		# change to local dir
	args = parse_args()
	eprint(args)


if __name__ == "__main__":
	tester()
