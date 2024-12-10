#!/usr/bin/python3


import os
import sys
import platform

from letters import eprint
from sd.easy_args import ArgMaster


LANGCODES = {'ar': 'Arabic', 'bg': 'Bulgarian', 'bn': 'Bengali', 'br': 'Breton', 'ca': 'Catalan', 'cs': 'Czech', 'da': 'Danish', 'de': 'German', 'el': 'Greek', 'en': 'English', 'eo': 'Esperanto', 'es': 'Spanish', 'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian', 'fi': 'Finnish', 'fr': 'French', 'gl': 'Galician', 'he': 'Hebrew', 'hi': 'Hindi', 'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian', 'it': 'Italian', 'ja': 'Japanese', 'ka': 'Georgian', 'kk': 'Kazakh', 'ko': 'Korean', 'lv': 'Latvian', 'mk': 'Macedonian', 'ml': 'Malayalam', 'nl': 'Dutch', 'no': 'Norwegian', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian', 'ru': 'Russian', 'sh': 'Serbo-Croatian', 'si': 'Sinhalese', 'sk': 'Slovak', 'sl': 'Slovenian', 'sq': 'Albanian', 'sv': 'Swedish', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tl': 'Tagalog', 'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'vi': 'Vietnamese', 'zh': 'Chinese'} # pylint: disable=line-too-long

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
    ['lang', '', list, ('en', 'English')],
    '''Language code or name.
    For example: --lang es or --lang Spanish will show you Spanish words.
    For more control, you can type the full set of language code + name like this:
    --lang <2 digit code> <language name>
    If you are typing the full set, then the language code and name must EXACTLY match the words used in Wiktionary or it won't detect the entries. For example, --lang sk Slovak will give you the Slovak language, but --lang sk Slovakian won't find anything. Go to https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to look up your language code and name.
    ''',
    ]

    frequencies = [\
    ['book', '', str],
    '''Location of a book file to use for additional frequency information.
    Must be in .txt format, NOT an e-reader format like .mobi - You can convert books to .txt format using the open-source Calibre program.
    The more a word appears in the boot, the more it will receive a boost in the adjusted frequency rankings.''',
    ['freq', '', str, ''],
    '''Change the location of the default frequency list. (Must match language with --lang)
    This is useful for specifying the Taiwanese or Brazilian version of the language.
    ''',
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
    ['multiline', '', str, 'autodetect'],
    '''
    True = Read one word per line. (A vertical list)
    False = Read multiple words per line (A book)
    '''
    ]

    display = [\
    ['csv', '', str],
    "Output data as csv filename instead of displaying. Example: --csv output.csv",
    ['min', '', float, 0],
    "Minimum total fpm to show a word candidate (not adjusted)",
    ['max', '', float, 0],
    "Maximum total fpm to show a word. (useful for filtering out super common words like: the)",
    ['length', '', int, 2],
    "Skip words under given length.",
    ['stars', '', bool, False],
    "Include abnormally high star words in the total when sorting or displaying",
    ['starval', '', int, 5],
    "Ratio of a conjugated word's fpm to the baseline to mark it with a star.",
    ['noentry', '', bool, False],
    '''Don't display the Wiktionary entry for each word (radically increases processing speed)''',
    ['threshold', '', float, 0.05],
    "Lowest fpm to still display a conjugation.\n--threshold 0.05 = (1 in 20 million words)",
    # At 250 words per minute for 4 hours a day, it would take around 333 days to come across a word at threshold
    # For a 1 fpm word, it would take 66 hours or 16+ days on average
    # For a .2 fpm word, it would take 83+ days
    # Words I look up in my native language are usually at around 0 to 0.3 fpm
    ]


    sorting = [\
    ['reverse', '', bool],
    "Reverse the word list",
    ['sort', '', bool],
    '''Loosely sorts the words from highest fpm to lowest
    applying a formula based on the original word's fpm and it's total derived fpm.
    ''',
    ['sortfactor', '', float, 0.8],
    '''
    A higher number biases the algorithm to sorting towards a word's total fpm.
    A lower number biases toward the original (input) word's fpm.
    Range: 0-1''',
    ]

    anki = [\
    ['anki', '', str, 'USER_DID_NOT_INPUT'],
    '''Location of your colection.anki2 or .apkg file to check to see if the search word already has a note.
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
    am.update(display, title="\nWhich words to display:")
    am.update(input_list, title="\nInput word list:")
    am.update(sorting, title="\nSorting the list:")
    am.update(anki, title="\nConnect with Anki")
    am.update(frequencies, title="\nFrequency lists:")
    am.update(positionals, title="Positional Arguments", positionals=True, hidden=True)
    am.update(hidden, "Used for testing purposes:", hidden=True)
    args = am.parse()


    # Language codes
    args.lang = [arg.lower().strip() for arg in args.lang]
    if not args.lang:
        print("Please enter a language. For example: --lang English")
        sys.exit(1)
    if args.lang[0] in ('bs', 'sr', 'hr'):
        print('''
        At last check, Wiktionary uses the code sh to refer to Serbo-Croatian languages.
        If you think this is a mistake, they have discussion pages here:
            https://en.wiktionary.org/wiki/Wiktionary:About_Serbo-Croatian
            https://en.wikipedia.org/wiki/Talk:Serbo-Croatian
        In the meantime, you can try using the following language code:
            --lang sh Serbo-Croatian --freq freq/sr.xz
        ''')
        input()

    if len(args.lang) == 1:
        args.lang = guess_lang(args.lang[0])
        if not args.lang:
            sys.exit(1)
        print("Set language to:", ' '.join(args.lang))



    # args.multiline
    choice = args.multiline.lower().strip()[:1]
    if choice == 'a':
        args.multiline = -1
    elif choice in 't1':
        args.multiline = 1
    elif choice in 'f0':
        args.multiline = 0
    else:
        print("Unknown args.multiline parameter")
        sys.exit(1)


    # Guess anki location
    args.anki = guess_anki(args.anki)


    # Checking
    status = False
    if args.filename and not os.path.exists(args.filename):
        print("Can't find file named:", args.filename)
    elif args.freq and not os.path.exists(args.freq):
        print("Can't find file:", args.freq)
    elif len(args.lang) != 2:
        print("Please enter the language in the format:", '--lang <code> <Name>')
        print("For example: --lang es spanish")
    elif len(args.lang[0]) != 2:
        print("Language codes must be 2 digits long")
    elif not 0 <= args.sortfactor <= 1:
        print("Sort factor must be between 0 and 1")
    elif args.csv and not args.csv.endswith('.csv'):
        print("csv output file must end with .csv to prevent accidentally overwriting the wrong file.")
    else:
        status = True
    if not status:
        sys.exit(1)

    if not args.freq:
        # Determine frequency file if not given
        if not args.wikifreq:
            lang = args.lang[0]
            if lang == 'sh':
                lang = 'sr'
                print("Defaulting to serbian frequency file.")
            args.freq = os.path.join('freq', lang + '.xz')
        else:
            args.freq = os.path.join('wikifreq', args.lang[0] + '.xz')
        eprint("Using frequency file:", args.freq)
        if not os.path.exists(args.freq):
            print("No frequency file found for language:", args.lang[0])
            status = False

    if not status:
        sys.exit(1)
    return args


def guess_anki(path):
    if path == 'USER_DID_NOT_INPUT':
        return None
    if path:
        return path     # user defined location

    if platform.system() == 'Windows':
        path = os.path.join(os.getenv('APPDATA'), 'Anki2')
    elif platform.system() == 'Linux':
        path = "~/.local/share/Anki2"
    elif platform.system() == 'Darwin':
        path = "~/Library/Application Support/Anki2"
    else:
        print("Unexpected system platform", platform.system())
        print("Please enter the .anki2 location manually using --anki <location>")
        sys.exit(1)
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        print("Could not find directory:", path)
        print("Please enter the .anki2 location manually using --anki <location>")
        sys.exit(1)
    path = os.path.join(path, 'User 1/collection.anki2')
    if not os.path.exists(path):
        print("Could not find .anki2 file :", path)
        print("Please enter the .anki2 location manually using --anki <location>")
        sys.exit(1)
    print("Using default anki location:", path)
    return path




def guess_lang(code):
    "Look at language code or language name and attempt to guess the pair"

    langnames = {val: key for key, val in LANGCODES.items()}


    # Spelling corrections
    spelling = dict(\
    Albanain="Albanian",\
    Aribic="Arabic",\
    Armenain="Armenian",\
    Basc="Basque",\
    Bengali="Bengali",\
    Bretonn="Breton",\
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
    Norwiegian="Norwegian",\
    Persain="Persian",\
    Polnish="Polish",\
    Portugeese="Portuguese",\
    Roumanian="Romanian",\
    Rusian="Russian",\
    SerboCroation="Serbo-Croatian",\
    Sinhalaese="Sinhalese",\
    Slovack="Slovak",\
    Slovenean="Slovenian",\
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
    Slovinian="Slovenian",\
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
    )



    # code -> language
    code = code.lower().strip()
    if code in LANGCODES:
        return [code, LANGCODES[code]]

    lang = code.title()
    # Fix spelling
    if lang in spelling:
        lang = spelling[lang]
    if lang in langnames:
        return [langnames[lang], lang]

    print("Unknown language:", code)
    print("If this is a real language that's not in my list you can try typing --lang <code> <name>")
    print("For example: --lang en English")

    print("\nThese are the current languages I know about:")
    print(' '.join(sorted(LANGCODES.values())))
    return False


def tester():
    os.chdir(sys.path[0])       # change to local dir
    args = parse_args()
    print(args)


if __name__ == "__main__":
    tester()
