#!/usr/bin/python3

import os
import re
import sys
import bz2
import csv
import lzma
import gzip
import json
import shutil
import string
import sqlite3

try:
    from unidecode import unidecode
except ModuleNotFoundError:
    print("Warning! Could not load unidecode module. Spelling correction disabled.")
    print("\tTo install unidecode, please run: pip install Unidecode\n")

import xml.etree.ElementTree as et
from time import perf_counter as tpc

from sd.common import rns, sig
from sd.columns import auto_columns

# Punctuation table
def gen_punct():
    punct = str.maketrans(dict.fromkeys(string.punctuation))
    for letter in "—¡¿":
        punct[ord(letter)] = None
    return punct

PUNCT = gen_punct()


def eprint(*args, **kargs):
    print(*args, file=sys.stderr, **kargs)


def strip_punct(word):
    "Strip punctuation and normalize word"
    return word.lower().strip().translate(PUNCT)


def strip_tags(text):
    # print("debug stripping", text)
    tree = et.fromstring(text)
    return et.tostring(tree, encoding='utf8', method='text').decode()


def get_wiktionary_filename():
    # Find best bz2 file to read
    matches = []
    for filename in os.listdir('.'):
        if re.match('^..wiktionary-.*multistream.xml.bz2', filename):
            matches.append(filename)
    if not matches:
        print("Please place a wiktionary dump with a filename similar to:")
        print("\tenwiktionary-20230601-pages-articles-multistream.xml.bz2 in the same directory as the program file.")
        sys.exit(1)
    matches.sort()
    return matches[-1]


def make_freq_table(filename):
    "Scan through frequency list and return words fpm"
    ext = os.path.splitext(filename.lower())[-1]

    if ext == '.bz2':
        f = bz2.open(filename, 'rt')
    elif ext == '.xz':
        f = lzma.open(filename, 'rt')
    elif ext == '.gz':
        f = gzip.open(filename, 'rt')
    elif ext == '.txt':
        f = open(filename, 'rt')
    else:
        print("Only frequency files in the format: .gz .bz2 or .txt are supported.")
        sys.exit(1)

    total = 0
    freq_table = dict()
    for line in f:
        line = line.strip().split()
        if line:
            word = line[0]
            if word.startswith('#'):
                continue
            count = int(line[1].replace(',', ''))
            total += count
            freq_table[word] = count

    f.close()

    return freq_table, total


def make_or_load_json(filename, function, *args):
    "Load json data set or run function to make it."
    if not os.path.exists(filename):
        print("Making", filename + '...')
        data = function(*args)
        with open(filename, 'w') as out:
            json.dump(data, out)
    else:
        start = loading(filename)
        data = json.load(open(filename))
        print_elapsed(start)
    return data


def make_data_base(dbname):
    if os.path.exists(dbname):
        os.remove(dbname)

    # Create database
    con = sqlite3.connect(dbname)
    cur = con.cursor()

    cur.execute("CREATE TABLE words(word, entry)")
    con.commit()
    con.close()

def timeit(func, *args, timeit_txt='Ran function in', **kargs):
    start = tpc()
    out = func(*args, **kargs)
    print(timeit_txt, rns(tpc() - start), 'seconds')
    return out


def dump_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_json(filename, ok_missing=False):
    if not os.path.exists(filename):
        if ok_missing:
            return dict()
        else:
            raise ValueError("Missing file!", filename)
    with open(filename) as f:
        return json.load(f)

def dump_roots(filename, roots):
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows([i[0]] + [y for x in i[1] for y in x] for i in roots.items())

def load_roots(filename):
    out = dict()
    with open(filename, 'r') as csv_file:
        for row in csv.reader(csv_file):
            out[row[0]] = list(zip(*[iter(row[1:])]*2))
    return out


def loading(name, header="Loading", newline=False):
    if newline:
        end = '\n'
    else:
        end = ' '
    eprint(header, name + '...', end=end, flush=True)
    return tpc()


def print_elapsed(start, newline=False):
    if newline:
        header = '\tDone in'
    else:
        header = ''
    eprint(header, rns(tpc() - start, digits=2), 'seconds', flush=True)


def make_spellings(words):
    "Make a dict of all words without accents"
    miss = dict()           # dict of misspelled words -> accented orignal
    if 'unidecode' in sys.modules:
        for word in words:
            basic = unidecode(word)
            if basic != word:
                if basic not in miss:
                    miss[basic] = []
                miss[basic].append(word)
    return miss



def make_word_tree(roots):
    '''Go through entire dictionary and build table of root words and all of their conjugations'''
    wt = dict()         # wordtree of: word->subs
    reverse = dict()    # Reverse tree of sub->final root
    index = 0


    for word in roots.keys():
        index += 1
        if not index % 100000:
            print("Building word tree:", rns(index), word + '...')

        def recurse(rword, seen=None, level=0):
            '''
            Recurse into the tags of each word
            Build up a line of words in seen until it reaches it's final root and dumps.
            '''

            for pair in roots.get(rword, []):

                root, tag = pair
                chain = (rword, tag, root)      # How a single word links to a root

                if level > 0 and 'plural' in tag:
                    continue

                if level == 0:
                    seen = []

                # Stop infinite loops
                if chain not in seen:
                    seen.append(chain)
                    recurse(root, seen, level=level+1)

                if level == 0 and seen:
                    final = seen[-1][-1]
                    if final not in wt:
                        wt[final] = set()

                    for triple in seen:
                        sub, tag, root = triple
                        wt[final].add(triple)

                        # Build the reverse tree
                        if sub not in reverse:
                            reverse[sub] = []
                        if final not in reverse[sub]:
                            reverse[sub].append(final)


        recurse(word)

    # Convert sets back to lists for storage
    for word in wt:
        wt[word] = list(wt[word])

    return wt, reverse

def fmt_fpm(fpm):
    return round(fpm, 1) if fpm < 10 else int(fpm)

def show_fpm(fpm):
    return (sig(fpm, digits=2) if fpm >= 0.1 else sig(fpm, digits=1)) + ' fpm'



class Tree:
    '''Load database and word tree derived from wiktionary'''

    def __init__(self, freq_file, lang, debug=False):
        self.debug = debug
        self.langcode = lang[0].lower()
        self.language = lang[1].title()
        self.cache = os.path.join('cache', self.langcode)
        os.makedirs(self.cache, exist_ok=True)

        dbname = os.path.join(self.cache, 'wiktionary.words.db')
        self.word_tree, self.reverse_tree = self.get_word_tree(dbname)

        start = loading("frequency table")
        self.freq, self.freq_total = make_freq_table(freq_file)
        print_elapsed(start)
        eprint("\tFound", rns(len(self.freq)), 'words in frequency table.')
        eprint("\t1 fpm is equivalent to", int(self.freq_total*1e-6), 'hits in this table.')

        start = loading("wikitionary database")
        self._con = sqlite3.connect(dbname)
        self._cur = self._con.cursor()
        self.words = {word[0] for word in self._cur.execute("SELECT word FROM words").fetchall()}
        print_elapsed(start)


        spelling_file = os.path.join(self.cache, 'spelling.json')
        if not os.path.exists(spelling_file):
            self.spellings = make_spellings(self.words)
            dump_json(spelling_file, self.spellings)
        start = loading("spelling tree")        # todo cache this
        self.spellings = load_json(spelling_file)

        print_elapsed(start)
        eprint("Loaded wiktionary database with", rns(len(self.words)), 'words available.')


    def check_spelling(self, word):
        '''Try to match a word without accents'''
        if word in self.words:
            return word
        if word in self.spellings:
            cans = self.spellings[word]
            if len(cans) != 1:
                print("\nDid you mean to type:", ' or '.join(cans), '?')
                cans = {self.get_fpm(word):word for word in cans}
                word = cans[sorted(cans.keys())[-1]]
                print("Returning the most common word:", word)
                return word
            print("\nCorrecting word:", word, 'to', cans[0])
            return cans[0]
        return word


    def root_entry(self, entry):
        "Scan dictionary entry looking for roots and tags"
        root = None         # Discovered root of word
        tags = []           # Pairs of (root word, tag (like 'es-verb form of')

        # Skip certain troublesome wiki sections
        section = ''            # Current Wiki Section
        bad_sections = ['etymology', 'pronunciation', 'related terms', 'further reading']


        for line in entry:
            #  Skip bad sections
            if re.match('===[^=]*===', line):
                section = line.strip().strip('=').lower()
            if section in bad_sections:
                continue

            # Find tags in Brackets
            for code in re.findall('{{[^{]*}}', line):
                # print("Section:", section, "Tag:", code)

                code = code.lower().strip('{{}}').split('|')
                code = list(filter(None, code))             # Filter blanks in list
                if not code:
                    print('Malformed line:', line)
                    continue
                tag = code[0]
                if tag.endswith(' of'):
                    # Disregard certain tags:
                    if re.findall(r'syn|synonym|pejorative', tag):
                        continue

                    if 'syn' in tag:
                        continue
                    if self.langcode in code:
                        if len(code) >= 3:
                            root = code[2]
                        else:
                            print('Cannot process:', code)
                            continue
                    else:
                        root = code[-1]

                    if '&' in root:
                        root = root.split('&')[0]
                    tags.append((root, tag))
        return tags


    def make_all_words(self, wiktionary_file, cur, con):
        "Go through wikitionary articles looking for spanish words and add their data to file."
        progress = 0

        entry = []              # Entry for a noun
        all_words = set()       # List of all words
        flag = False            # Start of Spanish section in each entry
        out = []                # Output ready to be synced with database
        found = 0               # Total entries found

        def commit():
            cur.executemany("insert into words (word, entry) values (?, ?)", out)
            con.commit()


        # Read the bz2 file and process into sqlite database
        update_rate = int(1e6)          # How often to display progress txt
        root_dict = dict()              # word -> root_entry(word)
        with bz2.open(wiktionary_file) as f:
            start = tpc()
            for line in f:
                # Track progress in file
                progress += 1
                if not progress % update_rate:
                    print('Reading line number', rns(progress), \
                          'at rate of', rns(progress / (tpc() - start)), 'lines per second.', \
                          'Found', rns(found, digits=2), 'entries so far...')


                # Look for title line
                line = line.decode().strip()
                if line.startswith("<title>"):
                    if entry:
                        flag = False
                        word = strip_tags(title_line)
                        if word in all_words:
                            print("Overwriting:", word)
                        else:
                            all_words.add(word)

                        # Append entry to out queue
                        found += 1
                        out.append((word, '\n'.join(entry)))
                        tags = self.root_entry(entry)



                        if len(out) >= 1e5:
                            commit()
                            out = []

                        if tags:
                            root_dict[word] = tags


                    # Clear the entry for new title
                    entry = []
                    title_line = line


                # Only add spanish section to entry
                if flag:
                    if line.startswith('==') and '===' not in line:
                        flag = False
                    else:
                        if not line.startswith('<'):
                            entry.append(line)

                else:
                    # Spanish section
                    if '==' + self.language + '==' in line:
                        flag = True

        commit()
        return root_dict

    def get_word_tree(self, dbname):
        #  Cache Files
        meta_file = os.path.join(self.cache, 'meta.json')
        tree_file = os.path.join(self.cache, 'tree.json')
        roots_file = os.path.join(self.cache, 'roots.csv')
        reverse_file = os.path.join(self.cache, 'reverse.json')


        # The meta file stores current state
        if os.path.exists(meta_file):
            meta = load_json(meta_file)

        else:
            meta = dict(words_finished=False, tree_finished=False)


        # Create sqlite database for words from wiktionary
        if not meta['words_finished']:
            if shutil.disk_usage(self.cache).free < 900e6:
                print("You should probably clear up some hard drive space before running this.")
                sys.exit(1)

            print("\nThe current language is set to:", self.langcode, self.language)
            print("You can change this by running the program with a different --lang setting.")
            print("Use --help for more info.\n")
            print("Building word database in", dbname)
            print("Please wait a few minutes... You will only have to do this once per language.\n")
            make_data_base(dbname)
            con = sqlite3.connect(dbname)
            cur = con.cursor()
            roots = self.make_all_words(get_wiktionary_filename(), cur, con)
            con.close()

            # Save roots to file
            # todo convert to csv for speed
            dump_roots(roots_file, roots)
            meta['words_finished'] = True
            dump_json(meta_file, meta)


        # Make the word tree associating words and roots
        if not meta['tree_finished'] or self.debug >= 3:
            roots = load_roots(roots_file)

            word_tree, reverse_tree = make_word_tree(roots)

            if word_tree:
                dump_json(tree_file, word_tree)
                dump_json(reverse_file, reverse_tree)
                meta['tree_finished'] = True
                dump_json(meta_file, meta)


        # Load word tree
        start = loading("word tree")
        word_tree = load_json(tree_file)
        reverse_tree = load_json(reverse_file)
        print_elapsed(start)
        return word_tree, reverse_tree

    def find_root(self, word, silent=False):
        '''Find the best root of a word'''
        # todo allow limited depth search
        if word not in self.word_tree:
            if word in self.reverse_tree:
                roots = self.reverse_tree[word]
                if not silent:
                    print('\nFound root of', word, '->', ', '.join(roots))
                if len(roots) == 1:
                    return roots[0]
                if not silent:
                    print('\nMultiple possible roots:')
                out = []
                for root in roots:
                    fpm = self.get_fpm(root)
                    out.append((fpm, root))
                    if not silent:
                        print(fmt_fpm(fpm), root)

                out.sort()
                root = out[-1][1]
                if not silent:
                    print('Chose root:', root)
                return root
        return None


    def get_fpm(self, word):
        hits = self.freq.get(word, 0)
        return hits / self.freq_total * 1e6


    def get_entry(self, word):
        if word in self.words:
            entry = self._cur.execute("select entry from words where word=" + "'" + word + "'").fetchone()
            return entry[0]
        return ''



    def calc_baseline(self, *words, silent=False):
        "Helper function of total_freq"
        baseline = 0.1
        for word in words:
            if not word:
                continue
            fpm = self.get_fpm(word)
            if fpm > baseline:
                baseline = fpm
        if self.debug >= 1 and not silent:
            print("Baseline =", show_fpm(baseline))

        return baseline


    def total_freq(self, word, branch=None, silent=False, threshold=0.05, \
        book=None, nostars=False, highstars=8):
        "Look up any word and return fpm of all conjugations combined."
        root = self.find_root(word, silent=True) or word


        book_total = 0      # Words in book
        high_total = 0      # Total of words with *
        skipped = 0         # Number of words with hits below threshold

        found = set()       # List of subs found
        subs = self.word_tree.get(root, []).copy()
        subs.append([root, '', ''])
        subs.sort()

        # Count up hits in frequency table
        all_hits = {sub:self.get_fpm(sub) for sub, _, _ in subs}
        total_hits = 0
        baseline = self.calc_baseline(root, word, branch, silent=silent)

        out = [['Conj:', 'FPM:', '', "Wikitags:"]]
        if book:
            out[0].insert(2, 'Book:')

        for sub, tag, subroot in subs:

            # Add up hits if it's a new sub
            hits = all_hits[sub]
            high = ''
            if sub not in found:
                bc = book.get(sub, 0) if book else 0        # book count of sub
                book_total += bc
                if branch:
                    # Match only words with tag linking back to branch
                    if subroot == branch or sub == branch:  # pylint:disable=consider-using-in
                        total_hits += hits
                    else:
                        found.add(sub)
                        continue
                else:
                    total_hits += hits

                # The original root gets an R, unsually common words get a * for further review
                high = 'R' if sub == root else ''
                if not high:
                    if hits / baseline >= highstars:
                        high_total += hits
                        high = '*' * int(((hits / baseline) / highstars)**0.5)

                # Skip lines for subs below threshold
                if hits < threshold:
                    if sub not in found:
                        skipped += 1
                    found.add(sub)
                    continue

            # Append tags only for duplicate subs
            # print(sub, tag, subroot, sub in found)
            tag = ' '.join((tag, subroot)).strip()
            if sub in found:
                if tag:
                    if book:
                        out.append(('', '', '', '', tag))
                    else:
                        out.append(('', '', '', tag))
            else:
                line = [sub, fmt_fpm(hits), high, tag]
                if book:
                    line.insert(2, bc or '')
                out.append(line)
            found.add(sub)


        # nostars mode removes * words from total
        if nostars:
            total_hits -= high_total


        # Show everything if not many skipped lines, else print lines above threshold
        if not silent:
            auto_columns(out, space=2, printme=True)
            if skipped:
                print("(skipped showing", skipped, 'conjugations below threshold)')
            if high_total and not nostars:
                print("(total without abnormally high * words is", str(fmt_fpm(total_hits - high_total)) + ')')

        return total_hits, book_total


    def close(self,):
        self._con.close()
