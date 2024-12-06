#!/usr/bin/python3

import os
import re
import sys
import csv
import time
import signal
from time import perf_counter as tpc


import myanki
from sd.common import rns
from sd.columns import auto_columns
from args import parse_args
from letters import strip_punct, COMMON_SYMBOLS, eprint
from tree import Tree, fmt_fpm, loading, show_fpm
from storage import make_or_load_json, dump_json


IS_WINDOWS = bool(os.name == 'nt')
if IS_WINDOWS and sys.flags.utf8_mode == 0:
    print("Windows users must run this program with: python3 -X utf8")
    sys.exit(1)


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



def detect_book(filename):
    "Count up how many words per line in text and determine if it should be read like a book or a list"
    wpl = []        # words per line
    with open(filename) as f:
        for line in f:
            line = line.split()
            wc = 0              # word count per line
            for word in line:
                # eprint(wc, word)
                if word.startswith('#'):
                    break
                wc += 1

            if wc:
                wpl.append(wc)
                # eprint(len(wpl), wc, line)
                if len(wpl) >= 2100:
                    # Sample error rate approaching 2%
                    break


    # chop off the first few dozen lines of book to avoid counting up non-prose intro
    # eprint(wpl)
    if len(wpl) >= 400:
        wpl = wpl[100:]
    wpl = sum(wpl) / len(wpl) if wpl else 0
    eprint("Detected an average of", int(round(wpl, 0)), "words per line from input file.")
    if wpl >= 16:
        return True
    return False



def get_words(filename, short_len, skiplines=0, multiline=-1):
    '''Read csv, txt or kindle clippings.txt
    multiline = 1 # True: Read many words per line
    multiline = 0 # False: Read one word per line
    multiline = -1 # Autodetect
    '''
    words = []
    book_mode = False           # Read multiple words per line


    def add_word(word):
        '''add word to table'''
        nonlocal words
        if word and not word.startswith('#'):
            word = strip_punct(word)
            if not word.strip():
                pass
            elif not book_mode and len(word) <= short_len:
                print('Skipping short word:', word)
            else:
                words.append(word)

    if not os.path.exists(filename):
        print("Filename does not exist!:", filename)
        return False


    # Try to read file as my clippings.txt first
    rc = read_clippings(filename, skiplines=skiplines)
    if rc:
        for word in rc:
            add_word(word)
        return words


    count = 0
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

        elif multiline >= 1 or (multiline == -1 and detect_book(filename)):
            eprint("Reading input file as book (many words per line):", filename)
            book_mode = True
            for line in f:
                for word in line.split():
                    count += 1
                    word = word.strip().lower()
                    if word:
                        add_word(word)
        else:
            eprint("Reading input file as txt (one word per line):", filename)
            for line in f:
                count += 1
                if count <= skiplines:
                    continue
                line = line.strip()
                if line:
                    word = line.split()[0].strip().lower()
                    add_word(word)


    # eprint("Found:", len(words), "unique words")
    return words


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


def load_anki(args):
    '''
    Get existing anki cards and make a searchable dict of Question words->Matching Notes
    '''
    anki = dict()
    loading("anki database", newline=True)
    notes = myanki.getnotes(args.anki)
    # print_elapsed(start, newline=True)
    eprint("\tFound", rns(len(notes)), 'notes.')
    decks = tuple(args.decks)   # Which deck's words to include.
    limit = args.ankilimit      # Number of words to search at start of card
    count = 0

    for nid, note in notes.items():
        if decks and note['deck'].startswith(decks):
            continue
        q = re.sub('<[^<]+>', ' ', note['question'])        # try to strip out any xml tags
        q = q.replace('&nbsp;', ' ').lower()            # These tags are the bane of my existence
        clean = strip_punct(q).split()
        if limit:
            clean = clean[:limit]
        anki[nid] = note
        count += 1

        # Using words as keys instead of entire questions improved search speed by 10x which means
        # rank_list can process at over 10k words per second now
        for word in clean:
            if word in anki:
                anki[word].add(nid)
            else:
                anki[word] = {nid}


    if count != len(notes):
        eprint("\tSelected", rns(count), "notes for searching.")

    return anki


def meta_usage(manual_mode):
    "Track program run count and remind to leave a review after 10, 30, 90... days and then once a year."
    def create():
        return dict(created=int(time.time()), manual=0, automatic=0, reminders=0, last_reminder=0)
    def increment(key):
        nonlocal meta
        if key not in meta:
            meta[key] = 0
        else:
            meta[key] += 1

    filename = os.path.join('cache', 'usage.json')
    meta = make_or_load_json(filename, create)
    if manual_mode:
        increment('manual')
    else:
        increment('automatic')


    total_usage = meta['manual'] + meta['automatic']
    usage_days = (time.time() - meta['created']) / 86400
    days_since_last_reminder = (time.time() - meta['last_reminder']) / 86400
    # print(days_since_last_reminder, meta['reminders'], usage_days)

    # Note: You can delete reviews.txt to make the reminders stop forever.
    if manual_mode and total_usage >= 4 and usage_days >= 4 and os.path.exists('reviews.txt') and \
    days_since_last_reminder >= min(256, 2 * meta['reminders']**1.414):
        increment('reminders')
        meta['last_reminder'] = int(time.time())
        print("\n\n")
        print(open('reviews.txt').read())

    dump_json(filename, meta)


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



def output_csv(ranked, ofile, book_freq):
    '''Ouput words as csv file.'''
    with open(ofile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow("Word Root FPM Total_FPM Book_Count".split())
        for word in ranked:
            writer.writerow([word.word, word.root, \
            fmt_fpm(word.fpm), fmt_fpm(word.derived), book_freq.get(word.word, '')])
    eprint("Writing csv file:", ofile)
    return True


class Word:
    "Calculate a word's root and fpm"

    def __init__(self, word, tree, args):
        self.extra = []
        if type(word) == list:
            self.extra = word[1:]
            word = word[0]
        self.word = word
        self.fpm = tree.get_fpm(word)
        self.root = tree.find_root(word, silent=True) or word
        self.derived, _ = tree.total_freq(word, silent=True, nostars=(not args.stars), highstars=args.starval)


    def check_anki(self, anki):
        '''Return nids that match word in anki'''
        if not anki:
            return []
        nids = []
        for word in (self.word, self.root):
            if word in anki:
                nids += anki[word]
        return list(set(nids))


    def print_anki(self, anki):
        '''Print each question found in anki cards'''
        out = []
        for nid in self.check_anki(anki):
            note = anki[nid]
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


    def adj(self, args):
        "calculate the adjustment"
        if self.fpm:
            return self.fpm * (self.derived / self.fpm) ** args.sortfactor
        else:
            return 0


    def skipped(self, args):
        # check if word should
        if args.max and self.derived > args.max:
            return True
        if args.min and self.derived < args.min:
            return True
        if args.skipanki and self.check_anki(args.anki):
            return True
        return False


    def fmt_fpm(self,):
        self.fpm = fmt_fpm(self.fpm)
        self.derived = fmt_fpm(self.derived)


    def print_entry(self, tree, root=True):
        if root:
            word = self.root or self.word
        else:
            word = self.word
        entry = tree.get_entry(word)
        if entry:
            print("\nWiktionary entry for:", word)
            print(entry)


    def print_info(self, tree, args, dupes=1, book_freq=None):
        '''Print the info of a word given'''

        print("Processing word:", self.word, 'at', show_fpm(self.fpm) + ':',
              "           (Card already in Anki)" if self.check_anki(args.anki) else '')

        # Show matches in anki database
        if args.anki:
            self.print_anki(args.anki)

        # Print total_freq tree and get bc (the book count)
        print('')
        _, book_count = tree.total_freq(self.word, book=book_freq, \
        threshold=args.threshold, nostars=(not args.stars), highstars=args.starval)
        print('')

        # Calculate the bookfpm
        book_fpm = book_count / book_freq['__TOTAL__'] * 1e6 if book_freq else 0

        # Get book frequency of word
        out = [' '.join((self.word, show_fpm(self.fpm))), '', '']
        if self.root and self.root != self.word:
            out[1] = ' '.join(('  Root:', self.root, show_fpm(tree.get_fpm(self.root))))

        # Total
        out.append('Total: ' + show_fpm(self.derived))
        if book_count:
            out.append('Book: ' + show_fpm(book_fpm))

        # Add dupes if greater than 1 (the loneliest number)
        if dupes > 1:
            out.append('Dupes: ' + str(dupes))


        # Calculate the adjustment based on book frequency and dupes.
        # By design this can only increase the word, never decrease it.
        # The root on book_fpm limits the impact of the book
        adjusted = (1 + (dupes - 1)/100)**3
        adjusted *= max((book_fpm / max(self.fpm, 0.001))**.2, 1)
        if adjusted > 1:
            out.append('Adj: ' + show_fpm(adjusted * self.derived))

        spaces = (' '*20, ' '*20, ' '*2, ' '*15, ' '*14)

        auto_columns([spaces, out], space=2, printme=True, wrap=999)
        print('_' * len(out))

        return True



def rank_list(words, tree, args, resort=True):
    "rank the list of words and return Word objects"
    eprint("Calculating the frequency and root of every word in the list of", rns(len(words)))

    processed = 0
    ranked = []     # words resorted by adj factor
    start = tpc()

    for word in words:
        word = Word(word, tree, args)
        processed += 1
        if not processed % 1000:
            wps = int(processed / (tpc() - start))
            eprint("Processed", rns(processed), 'words at', rns(wps), 'per second:', word.word)
        if not word.skipped(args):
            ranked.append((word.adj(args), word))

    if resort:
        if args.sort:
            ranked.sort(key=lambda x: x[0], reverse=True)
        if args.reverse:
            ranked.sort(key=lambda x: x[0])


    # Return the sorted list of words
    return [row[1] for row in ranked]



def rank_book(filename, tree, args):
    "Output table of entire book with word, occurences, fpm"

    eprint("\n")
    if os.path.exists(filename):
        eprint("Loading:", filename)
        book = get_freq_table(filename)
    else:
        eprint("Can't find filename:", filename)
        return False

    total = book.pop('__TOTAL__')

    # Get words
    words = [[key, val] for key, val in book.items()]
    if not words:
        eprint(r"Error. Could not find any words ¯\_(ツ)_/¯ ")
        return False
    words.sort(key=lambda x: x[1], reverse=True)
    eprint("Found", rns(len(words)), "unique words in book out of", rns(total), 'total words.\n')
    words = rank_list(words, tree, args)


    written = 0
    eprint("\n")
    ofile = os.path.basename(filename) + '.csv'
    with open(ofile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow("Word Count Book_FPM FPM Ratio Root Total_FPM".split())

        for word in words:
            count = word.extra[0]
            book_fpm = fmt_fpm(count / total * 1e6)
            fpm_ratio = book_fpm / word.fpm if word.fpm else -1
            fpm_ratio = int(fpm_ratio) if fpm_ratio >= 10 else round(fpm_ratio, 2)
            word.fmt_fpm()

            writer.writerow([word.word, count, book_fpm, word.fpm, fpm_ratio, word.root, word.derived])
            written += 1


    eprint(rns(written), "words written to:", ofile)
    return True


def arrows(word):
    up = word.count('\x1b[A')
    down = word.count('\x1b[B')
    return up - down


def manual_input(tree, args, book_freq):
    "Manually input words and check them"

    word = None
    history = []
    count = 0
    while True:
        count += 1
        print("")
        if not word:
            print('\n'*3)
            if count == 1:
                print("Common accented characters ready to copy-paste:\n")
            print(COMMON_SYMBOLS, '\n')
            word = user_word('Input word or type q to quit: ')


        # Load word from history using up/down arrows
        if arrows(word):
            try:
                word = history[-(arrows(word))]
            except IndexError:
                print(history[-5:])
                word = ''
                continue
            print("Replaying word:", word)
        elif len(word.strip()) > 1:
            history.append(word)

        word = word.strip().lower()

        # Commands
        if word == 'q':
            return True
        if word == 'w' and history:
            # Redo the last word and print entry
            word = Word(tree.check_spelling(history[-1]), tree, args)
            word.print_entry(tree, root=False)
            word = None
            continue

        # Check for bad words
        if ' ' in word:
            print("Multiple word phrases are not supported.")
            word = ''
        if not word or word == 'w':
            word = None
            continue

        # Print the info for the word
        word = Word(tree.check_spelling(word), tree, args)
        word.print_info(tree, args, book_freq=book_freq)

        # If the Wiktionary entry is available, print it on request
        if not args.noentry and tree.get_entry(word.root):
            i = user_word("\nPress enter to show root entry, type w to show word entry, or type new word: ")
            if i.lower() == 'w':
                word.print_entry(tree, root=False)
                word = None
            elif not i:
                word.print_entry(tree)
                word = None
            else:
                word = i
        else:
            word = None


def process_list(words, tree, args, book_freq):
    "Process a list of words"
    # Cancel out a word in words for each word in ignore
    # Done before duplicates, because that will remove words
    if args.ignore:
        words = ignore_words(words, args.ignore)

    # Look for duplicates
    dupes = dict()
    unranked = []
    for word in words:
        if word in dupes:
            dupes[word] += 1
        else:
            dupes[word] = 1
            unranked.append(word)


    # Sort the words into a list of ranked Word objects
    ranked = rank_list(unranked, tree, args)

    if args.csv:
        return output_csv(ranked, args.csv, book_freq)


    eprint("\n\nDone! Here are the words with definitions.")
    for line in open('warning.txt').readlines():
        eprint(line.strip())
        eprint("")

    eprint("Processing", len(ranked), "words...")
    if not args.noentry and len(ranked) >= 1000:
        eprint("\nWarning: This is going to take a long ass time...")
        eprint("May I suggest using --noentry to print words without their definitions?\n")


    # Output words and definitions
    count = 0
    start = tpc()
    for word in ranked:
        count += 1
        if not count % 100:
            wps = count / (tpc() - start)
            eprint("Processed word number", count, "at", wps, "per second.")

        print('\n' * 5)
        word.print_info(tree, args, dupes=dupes.get(word.word), book_freq=book_freq)
        if not args.noentry:
            word.print_entry(tree)

    eprint("Done.")
    return True


def main():
    args = parse_args()

    # Load data
    tree = Tree(args.freq, args.lang, debug=args.debug)
    args.anki = load_anki(args) if args.anki else dict()
    eprint("\n")

    # Load a book to use as a frequency source (optional)
    book_freq = dict()
    if args.book and os.path.exists(args.book):
        book_freq = make_or_load_json(\
            os.path.join('cache', os.path.basename(args.book) + '.json'), \
            get_freq_table, args.book)


    if args.rankbook:
        return rank_book(args.rankbook or args.filename, tree, args)


    # Get word list
    if args.wikiroots:
        words = list(tree.word_tree.keys())
    elif args.wikiwords:
        words = tree.words
    elif args.filename:
        # Get words from txt or csv file
        words = get_words(args.filename, args.length, skiplines=args.skiplines, multiline=args.multiline)
        eprint("Found", len(words), "words in input file:", args.filename)
    else:
        # Manual mode
        meta_usage(False)
        eprint("No filename specified, but you can manually type in a word below if you wish:")
        return manual_input(tree, args, book_freq)


    # Process word list (automatic mode)
    meta_usage(True)
    process_list(words, tree, args, book_freq)


    return True



if __name__ == "__main__":
    os.chdir(sys.path[0])       # change to local dir
    if '-lang' not in ' '.join(sys.argv[:]).lower():
        print("Language set to default: es Spanish")
        print("Use --lang to change\n")

    if not os.access('.', os.W_OK):
        print("Directory", os.getcwd(), "must be writable to store a cached version of the wikitionary database.")
        sys.exit(1)
    # Scan frequency table into memory (no advantage to json caching)
    sys.exit(not main())
