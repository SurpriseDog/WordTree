#!/usr/bin/python3

import os
import re
import sys
import csv
import signal
import myanki
from sd.common import rns
from sd.easy_args import ArgMaster
from sd.columns import auto_columns
from tree import Tree, make_or_load_json, fmt_fpm, loading, print_elapsed, strip_punct, eprint, show_fpm


IS_WINDOWS = bool(os.name == 'nt')
if IS_WINDOWS and sys.flags.utf8_mode == 0:
    print("Windows users must run this program with: python3 -X utf8")
    sys.exit(1)


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
    ['lang', '', list, ('es', 'Spanish')],
    '''Language code and name. Example: --lang en English
    Go to https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to look up your language code.
    ''',
    ]

    optionals = [\
    ['book', '', str],
    '''Location of a book file to use for additional frequency information.
    Must be in .txt format, NOT an e-reader format like .mobi
    The more a word appears in the boot, the more it will receive a boost in the adjusted frequency rankings.''',
    ['anki', '', str],
    '''Location of your .anki2 or .apkg file to check to see if the search word already has a note.
    Only searches the first few words of the front card to avoid any example sentences.
    If you get a 'Database is Locked' error, then you need to close Anki first
    or simply export the cards you wish to search to a .apkg file (recommended)
    ''',
    ['freq', '', str, ''],
    '''Change the location of the default frequency list. (Must match language with --lang)
    This is useful for specifying the Taiwanese or Brazilian version of the language.
    ''',
    ['wikifreq', '', bool, False],
    '''Use frequency lists gathered from Wikipedia instead of subtitles. This is useful if you want to focus more on the written word instead of the spoken word.''',
    ]

    input_list = [\
    ['ignore', '', str],
    "Ignore words on this list.\nEach word on the ignore list cancels out one word on the word list.",
    "Debugging mode.",
    ['wikiroots', '', bool, False],
    "Why supply your own word list when you can rank every single root word in the dictionary?",
    ['wikiwords', '', bool, False],
    "Show every word in the dictionary.\n(This will take awhile unless you combine it with --csv)",
    ['skiplines', '', int, 0],
    "Skip lines at start of words list. (Helpful if you want to resume a session later)",
    ]

    display = [\
    ['csv', '', str],
    "Output data as csv filename instead of displaying. Example: --csv output.csv",
    ['skipanki', '', bool],
    "Skip any cards that already in anki database instead of just noting them.\nMust combine with --anki",
    ['min', '', float, 0],
    "Minimum total fpm to show a word candidate (not adjusted)",
    ['max', '', float, 0],
    "Maximum total fpm to show a word. (useful for filtering out super common words like: the)",
    ['length', '', int, 2],
    "Skip words under given length.",
    ['nostars', '', bool, False],
    "Don't consider abnormally high star words when sorting or displaying",
    ['highstars', '', int, 5],
    "Ratio of a conjugated word's fpm to the baseline to mark it with a star.",
    ['noentry', '', bool, False],
    "Don't display the Wiktionary entry for each word",
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
    Range 0-1''',
    ]

    hidden = [\
    ['debug', '', bool, False],
    ]



    am = ArgMaster(\
        usage='<txt/csv word list>, --options...',
        description="Scan Wiktionary to determine a word's root and frequency of conjugations in fpm (Frequency per million words)")
    am.update(language, title="Language:")
    am.update(optionals, title="Optional arguments:")
    am.update(input_list, title="Input word list:\n(These options control how the optional input word list is processed.)")
    am.update(sorting, title="Sorting:")
    am.update(display, title="Which words to display:")
    am.update(positionals, title="Positional Arguments", positionals=True, hidden=True)
    am.update(hidden, "Used for testing purposes:", hidden=True)
    args = am.parse()


    args.lang = [strip_punct(arg.lower().strip()) for arg in args.lang]


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
    else:
        status = True

    if not args.freq:
        # Determine frequency file if not given
        if not args.wikifreq:
            args.freq = os.path.join('freq', args.lang[0] + '.xz')
        else:
            args.freq = os.path.join('wikifreq', args.lang[0] + '.xz')
        eprint("Using frequency file:", args.freq)
        if not os.path.exists(args.freq):
            print("No frequency file found for language:", args.lang[0])
            status = False

    if status:
        return args
    sys.exit(1)
    return None     # Needed for Pylint


def read_clippings(filename, skiplines=0):
    "Detect My Clippings format and return words if true."
    kindle = 0      # Count of lines like kindle format
    count = 0       # Count of all lines
    prev = ''       # Previous line
    prev2 = ''      # 2 lines back
    words = []      # list of words collected

    def test_ratio():
        "Test the ratio of kindle lines to other lines"
        # Expected 60% of lines to match tests
        ratio = kindle / count
        return bool((ratio >= 0.2 and "clippings" in filename.lower()) or ratio >= 0.3)



    # Read a sample of the file and determine if it's a kindle file
    with open(filename) as f:
        for line in f:
            count += 1
            line = line.strip()
            if line == "==========":
                if len(prev.split()) == 1:
                    if count >= skiplines:
                        words.append(prev)
                    kindle += 0.5           # a single word on a line before ===== only suggests kindle format
                if prev2 == "":
                    kindle += 2
            elif "Your Highlight" in line or line.startswith("- Bookmark on Page "):
                kindle += 1
            if count == 100:
                if not test_ratio():
                    return None

            prev2 = prev
            prev = line
            # print(int(kindle / count * 100), line)

    if not test_ratio():
        return None
    eprint("Detected Kindle My clippings.txt format")
    return words





def get_words(filename, short_len, skiplines=0):
    '''Read csv, txt or kindle clippings.txt'''
    words = []
    duplicates = dict()         # Count of duplicates word->count

    def add_word(word):
        '''add word to table if checks pass and count up duplicates'''
        nonlocal words, duplicates
        if word and not word.startswith('#'):
            word = strip_punct(word)
            if not word.strip():
                pass
            elif len(word) <= short_len:
                print('Skipping short word:', word)
            elif word in words:
                duplicates[word] = duplicates.get(word, 0) + 1
            else:
                words.append(word)

    if not os.path.exists(filename):
        print("Filename does not exist!:", filename)
        return False
    count = 0

    # Try to read file as my clippings.txt first
    rc = read_clippings(filename, skiplines=skiplines)
    if rc:
        for word in rc:
            add_word(word)
        return words, duplicates


    with open(filename) as f:
        if filename.lower().endswith('.csv'):
            eprint("Reading input file as csv:", filename)
            reader = csv.reader(f)
            for line in reader:
                count += 1
                if count <= skiplines:
                    continue
                word = line[0].strip().lower()
                add_word(word)

        else:
            eprint("Reading input file as txt:", filename)
            for line in f:
                count += 1
                if count <= skiplines:
                    continue
                line = line.strip()
                if line:
                    word = line.split()[0].strip().lower()
                    add_word(word)
    return words, duplicates


def get_freq_table(filename):
    "Scan words in filename and convert to frequency table of word->freq"
    freq = dict()
    total = 0

    with open(filename) as f:
        for line in f:
            for word in line.split():
                total += 1
                word = strip_punct(word)
                freq[word] = freq.get(word, 0) + 1

    freq['__TOTAL__'] = total
    return freq


def rank_words(words, tree, args):
    '''Loosely rank a list of words by fpm and derived fpm'''
    ranked = []
    count = 0

    update = int(1e5)
    for word in words:
        count += 1
        if not count % update:
            print(rns(count))

        derived, _ = tree.total_freq(word, silent=True, nostars=args.nostars, highstars=args.highstars)

        # Average the original with the derived fpm so crazy words don't mess up the rankings too much
        fpm = tree.get_fpm(word)
        if fpm:
            adj = fpm * (derived / fpm)**args.sortfactor

            if args.max and derived >= args.max:
                continue

            if derived >= args.min:
                # print('debug', derived, word)
                ranked.append((adj, word))

    if args.sort:
        ranked.sort(reverse=True)
    if args.reverse:
        ranked.reverse()
    if count >= update:
        eprint("Done!")

    return ranked


def output_csv(ranked, tree, args, book_freq):
    '''Ouput words as csv file.'''
    filename = args.csv
    eprint("Writing csv file:", filename)

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow("Word FPM Total_FPM Book_Count".split())
        for _, word in ranked:
            fpm = tree.get_fpm(word)
            derived, _ = tree.total_freq(word, silent=True, nostars=args.nostars, highstars=args.highstars)

            writer.writerow([word, fmt_fpm(fpm), fmt_fpm(derived), book_freq.get(word, 0)])
    return True


def print_entry(word, tree):
    entry = tree.get_entry(word)
    if entry:
        print("\nWiktionary entry for:", word)
        print(entry)



def load_anki(filename, limit):
    '''
    Get existing anki cards and make a searchable dict
    limit = number of words to search at start of card
    '''
    anki = dict()
    start = loading("anki database", newline=True)
    notes = myanki.getnotes(filename).values()
    print_elapsed(start, newline=True)
    eprint("\tFound", rns(len(notes)), 'notes.')

    # Make dict of searchable to questions
    for note in notes:
        q = re.sub('<[^<]+>', '', note['question'])     # try to strip out any xml tags
        clean = strip_punct(q)
        clean = tuple(clean.split()[:limit])
        anki[clean] = note
        # print(clean, '==', note)

    return anki


def ignore_words(words, ignore_list):
    out = []
    ignore, _ = get_words(ignore_list, 0)
    for word in words:
        if word in ignore:
            # print("Ignoring:", word)
            ignore.remove(word)
        else:
            out.append(word)
    return out


def check_anki(word, anki):
    '''Return questions match word in anki'''
    if word and anki:
        return [anki[key] for key in anki if word in key]
    return []

def print_anki(found):
    '''Print each question found in anki cards'''
    out = []
    for note in found:
        # print(note)
        out.append([])
        out.append(('Deck:', note['deck']))
        ques = note['question']
        queue = note['queue']
        if queue == -1:
            ques = 'Suspended: ' + ques
        elif queue == 0:
            ques = 'New: ' + ques
        if len(ques) > 256:
            ques = ques[:256] + '...'
        out.append(('Question:', ques))
    auto_columns(out, space=2, printme=True)


def user_word(text):
    "Get user input while ignoring ctrl-C or Z"
    def interrupt(*_):
        print("\nType q to quit")

    if IS_WINDOWS:
        word = input(text)
    else:
        signal.signal(signal.SIGINT, interrupt)     # Catch Ctrl-C
        signal.signal(signal.SIGTSTP, interrupt)    # Catch Ctrl-Z
        word = input(text)
        signal.signal(signal.SIGINT, lambda *args: sys.exit(1))
        signal.signal(signal.SIGTSTP, lambda *args: sys.exit(1))
    return word.strip()


def main():
    args = parse_args()

    # Load data
    words = []              # List of words to process
    duplicates = dict()     # Duplicate words in list
    anki = load_anki(args.anki, limit=9) if args.anki else dict()
    tree = Tree(args.freq, args.lang, debug=args.debug)
    book_freq = dict()      # Load a book to use as a frequency source (optional)
    if args.book and os.path.exists(args.book):
        book_freq = make_or_load_json(os.path.join('cache', os.path.basename(args.book) + '.json'), \
                    get_freq_table, args.book)


    # Get word list
    if args.wikiroots:
        words = list(tree.word_tree.keys())
    elif args.wikiwords:
        words = tree.words
    elif args.filename:
        # Get words from txt or csv file
        words, duplicates = get_words(args.filename, args.length, skiplines=args.skiplines)
    if args.ignore:
        words = ignore_words(words, args.ignore)    # Cancel out a word in words for each word in ignore
    if args.filename:
        eprint("Found", len(words), "words in input file:", args.filename)
    else:
        eprint("No filename specified, but you can manually type in a word below if you wish:")


    def print_info(word, root, margin=2):
        '''Print the info of a word given'''
        # todo just pass the word
        fpm, _ = tree.total_freq(word, silent=True, nostars=args.nostars, highstars=args.highstars)


        # Check anki
        found = check_anki(word, anki) + check_anki(root, anki)

        # Skip if found cards are not suspended
        if found and args.skipanki:
            # Skip if cards are more than just suspended
            if not {note['queue'] for note in found} == '-1':
                return False

        print("\n" * margin, end='')
        print("Processing word:", word, 'at', show_fpm(tree.get_fpm(word)) + ':',
              "           (Card already in Anki)" if found else '')
        print_anki(found)
        tree.find_root(word, silent=False)


        # Print total_freq tree
        print("")
        fpm, bc = tree.total_freq(word, book=book_freq, threshold=args.threshold, nostars=args.nostars, highstars=args.highstars)
        book_fpm = bc / book_freq['__TOTAL__'] * 1e6 if book_freq else 0


        # Get book frequency of word
        out = [' '.join((word, show_fpm(tree.get_fpm(word)))), '', '']
        if root and root != word:
            out[1] = ' '.join(('  Root:', root, show_fpm(tree.get_fpm(root))))

        out.append('Total: ' + show_fpm(fpm))
        if bc:
            out.append('Book: ' + show_fpm(book_fpm))

        dupes = duplicates.get(word, 0)
        if dupes:
            out.append('Dupes: ' + str(dupes))


        # Calculate the adjustment based on book frequency and dupes.
        # By design this can only increase the word, never decrease it.
        # The root on book_fpm limits the impact of the book
        dupes_percent = dupes / (len(words) + 1) # close enough, lol
        adjusted = (1 + dupes_percent)**3 * max((book_fpm / max(fpm, 0.001))**.2, 1)
        adjusted = fpm * adjusted

        if adjusted != fpm:
            out.append('Adj: ' + show_fpm(adjusted))
        else:
            out.append('Freq: ' + show_fpm(fpm))

        # spaces = (' '*50, ' '*15, ' '*14)
        spaces = (' '*20, ' '*30, ' '*4, ' '*15, ' '*14)
        # spaces = (word.replace(' ', '-') for word in spaces)

        # print('debug out =', repr(out))
        auto_columns([spaces, out], space=2, printme=True, wrap=999)
        print('_' * len(out))
        return True


    # Manual mode
    if not words:
        word = None
        while True:
            print("\n\n")
            if not word:
                word = user_word('Input word or type q to quit: ')

            word = word.strip().lower()
            if word == 'q':
                return True
            if not word:
                continue

            if word:
                word = tree.check_spelling(word)
                root = tree.find_root(word, silent=False)
                print_info(word, root)

            if not args.noentry and tree.get_entry(word):
                i = user_word("\nPress enter to show entry or type new word: ")
                if not i:
                    print_entry(root or word, tree)
                    word = None
                else:
                    word = i
            else:
                word = None


    eprint("\n\nCalculating the frequency and root of every word in the list.")
    ranked = rank_words(words, tree, args)  # Go through list of words

    if args.csv:
        return output_csv(ranked, tree, args.csv, book_freq)


    eprint("\n\nDone! Here are the words with definitions.")
    for line in open('warning.txt').readlines():
        eprint(line.strip())

    for _derived, word in ranked:
        root = tree.find_root(word, silent=True)
        print_info(word, root, margin=5)
        if word:
            if not args.noentry:
                print_entry(root or word, tree)
    return True

open('warning.txt').readlines()


if __name__ == "__main__":
    os.chdir(sys.path[0])       # change to local dir
    if not '-lang' in ' '.join(sys.argv[:]).lower():
        print("Language set to default: es Spanish")
        print("Use --lang to change\n")

    if not os.access('.', os.W_OK):
        print("Directory", os.getcwd(), "must be writable to store a cached version of the wikitionary database.")
        sys.exit(1)
    # Scan frequency table into memory (no advantage to json caching)
    sys.exit(not main())
