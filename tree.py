#!/usr/bin/python3

import os
import re
import sys
import bz2
import lzma
import gzip
import shutil
import sqlite3

import xml.etree.ElementTree as et
from time import perf_counter as tpc

from sd.common import rns, sig, rint
from sd.columns import auto_columns

import storage
from letters import eprint, make_spellings
from storage import dump_json, load_json, loading, print_elapsed


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
        print("Link: https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2") # pylint: disable=line-too-long
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
        if len(line) >= 2:
            word = line[0]
            if word.startswith('#'):
                continue
            count = int(line[1].replace(',', ''))
            total += count
            freq_table[word] = count
        # if not total % 1000:
        #   print(total)

    f.close()

    return freq_table, total


def make_data_base(dbname):
    if os.path.exists(dbname):
        os.remove(dbname)

    # Create database
    con = sqlite3.connect(dbname)
    cur = con.cursor()

    cur.execute("CREATE TABLE words(word, entry)")
    con.commit()
    con.close()



def make_word_tree(roots):
    '''Go through entire dictionary and build table of root words and all of their conjugations'''
    wt = dict()         # wordtree of: word->subs
    reverse = dict()    # Reverse tree of sub->final root
    index = 0


    print("\n")
    for word in roots.keys():
        index += 1
        if not index % 10000:
            print("Building word tree:", rns(index), word)

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
        overall_start = tpc()

        self.debug = debug
        self.langcode = lang[0].lower()
        self.language = lang[1].title()
        self.cache = os.path.join('cache', self.langcode)
        os.makedirs(self.cache, exist_ok=True)

        dbname = os.path.join(self.cache, 'wiktionary.words.db')
        self.word_tree, self.reverse_tree = self.get_word_tree(dbname)


        # Can't be threaded because of large data size
        start = loading("frequency table")
        self.freq, self.freq_total = make_freq_table(freq_file)
        print_elapsed(start)
        eprint("\tThis table was created by scanning at least", rns(self.freq_total), 'total words.')
        eprint("\tFound", rns(len(self.freq)), 'unique words in frequency table.')
        eprint("\t1 fpm is equivalent to", rns(self.freq_total*1e-6), 'hits in this table.')


        start = loading("wikitionary database")
        self._con = sqlite3.connect(dbname)
        self._cur = self._con.cursor()
        self.words = {word[0] for word in self._cur.execute("SELECT word FROM words").fetchall()}
        print_elapsed(start)


        spelling_file = os.path.join(self.cache, 'spelling.json')
        if not os.path.exists(spelling_file):
            self.spellings = make_spellings(self.words)
            dump_json(spelling_file, self.spellings)
        start = loading("spelling tree")
        self.spellings = load_json(spelling_file)   # Seems to be faster directly

        print_elapsed(start)
        eprint("Loaded wiktionary database with", rns(len(self.words)), 'words available.')
        if tpc() - overall_start < 60:
            print("Total tree class loading time:", rns(tpc() - overall_start), 'seconds')


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
                    print('Malformed line in text:', line)
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
                            root = code[2].replace('[', '').replace(']', '')
                        else:
                            print('Cannot process:', code)
                            continue
                    else:
                        root = code[-1]

                    if '&' in root:
                        root = root.split('&')[0]
                    tags.append((root, tag))
        return tags


    def make_all_words(self, dbname):
        "Go through wikitionary articles looking for spanish words and add their data to file."
        con = sqlite3.connect(dbname)
        cur = con.cursor()
        wiktionary_file = get_wiktionary_filename()

        def commit():
            cur.executemany("insert into words (word, entry) values (?, ?)", out)
            con.commit()

        print("Building word database in", dbname)
        print("Reading from file:", wiktionary_file)
        # todo update this number from most recent wiki dump
        expected = 200 * (os.path.getsize(wiktionary_file) / 1000)
        print("\nThere should be around", rns(expected * 0.9), 'to', rns(expected * 1.1), \
        "lines of xml text to process.")
        print("Please wait a few minutes... You will only have to do this once per language:\n")


        progress = 0                # Track progress in file
        update_rate = 10**(8 if self.debug else 6)      # How often to display progress txt
        root_dict = dict()          # word -> root_entry(word)
        entry = []                  # Entry for a noun
        all_words = set()           # Set of all words
        flag = False                # Start of requested language section in each entry
        out = []                    # Output ready to be synced with database
        found = 0                   # Total entries found
        start = tpc()               # Start time


        # Read the bz2 file and process into sqlite database
        with bz2.open(wiktionary_file) as f:
            for line in f:
                progress += 1
                if not progress % update_rate:
                    print('Read', rns(progress), 'lines at a rate of', rns(progress / (tpc() - start)), \
                    'lines per second.', 'Found', rns(found), 'entries so far...')


                # Look for title line
                line = line.decode().strip()
                if line.startswith("<title>"):
                    if entry:
                        flag = False
                        word = strip_tags(title_line).replace('[', '').replace(']', '')
                        if word in all_words:
                            print("Overwriting:", word)
                        else:
                            all_words.add(word)

                        # Append entry to buffer and sync with database every so many entries
                        found += 1
                        out.append((word, '\n'.join(entry)))
                        if len(out) >= 1e5:
                            commit()
                            out = []

                        # Process tags from entry
                        tags = self.root_entry(entry)
                        if tags:
                            root_dict[word] = tags

                    # Clear the entry for new title
                    entry = []
                    title_line = line       # From the last read title

                # Only add requested language section to entry
                if flag:
                    if line.startswith('==') and '===' not in line:
                        flag = False
                    else:
                        if not line.startswith('<'):
                            entry.append(line)
                else:
                    if '==' + self.language + '==' in line:
                        flag = True

        commit()
        con.close()
        print("Read", f"{progress:,}", "lines in", rns((tpc() - start) / 60), 'minutes')
        print("Averaged", rint(progress / (os.path.getsize(wiktionary_file) / 1000)), 'lines per KB')

        return root_dict


    def get_word_tree(self, dbname):
        #  Cache Files
        meta_file = os.path.join(self.cache, 'meta.json')
        tree_file = os.path.join(self.cache, 'tree.json')
        roots_file = os.path.join(self.cache, 'roots.json')
        reverse_file = os.path.join(self.cache, 'reverse.json')


        # The meta file stores current state
        if os.path.exists(meta_file):
            meta = load_json(meta_file)

        else:
            meta = dict(words_finished=False, tree_finished=False)


        # Create sqlite database for words from wiktionary
        if not meta['words_finished']:

            # Current "en" folder is 751 MB so I'm setting a minimum HDD space of a gig
            if shutil.disk_usage(self.cache).free < 1e9:
                print("You should probably clear up some hard drive space before running this.")
                sys.exit(1)

            print("\nThe current language is set to:", self.langcode, self.language)
            print("You can change this by running the program with a different --lang setting.")
            print("Use --help for more info.\n")

            make_data_base(dbname)
            roots = self.make_all_words(dbname)

            # Save roots to file
            dump_json(roots_file, roots)
            meta['words_finished'] = True
            dump_json(meta_file, meta)


        # Make the word tree associating words and roots
        if not meta['tree_finished'] or self.debug >= 3:
            roots = load_json(roots_file)
            word_tree, reverse_tree = make_word_tree(roots)

            if word_tree:
                # todo write tree_file directly to csv directly after testing
                print("Writing word tree to .json")
                dump_json(tree_file, word_tree)
                print("Writing reverse word tree to .json")
                dump_json(reverse_file, reverse_tree)
                meta['tree_finished'] = True
                dump_json(meta_file, meta)
            else:
                eprint('''
            The word tree is empty.
            Double check that the --lang arguments were correct before deleting the cache folder
            and trying again. Sometimes languages are labelled differently in Wiktionary.
            For example: the Bosnian language is under the label: Serbo-Croatian with the code sh
            So to look for Bosnian words using the Bosnian frequency table,
            I would have to run: --lang sh Serbo-Croatian --freq freq/bn.xz
                ''')
                sys.exit(1)


        # Load word tree
        start = loading("word tree")
        word_tree = storage.convert_and_load(tree_file, chunk=3, use_json=False)
        print_elapsed(start)

        start = loading("reverse tree")
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
        book=None, nostars=True, highstars=8):
        "Look up any word and return fpm of all conjugations combined."
        root = self.find_root(word, silent=True) or word


        book_total = 0      # Words in book
        high_total = 0      # Total of words with *
        skipped = 0         # Number of words with hits below threshold

        found = set()       # List of subs found (and added to the total_hits)
        subs = self.word_tree.get(root, []).copy()
        subs.append((root, '', ''))
        subs.sort()

        # print('subs', subs)
        # print('word', word, 'branch', branch)

        # Count up hits in frequency table
        all_hits = {sub:self.get_fpm(sub) for sub, _, _ in subs}
        total_hits = 0
        baseline = self.calc_baseline(root, word, branch, silent=silent)

        # print(all_hits, total_hits)

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
                        found.add(sub)
                    else:
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
            if high_total:
                if nostars:
                    print("Total with stars words would have been:", fmt_fpm(total_hits + high_total), 'fpm')
                else:
                    print("(total without abnormally high * words is", str(fmt_fpm(total_hits - high_total)) + ')')

        return total_hits, book_total


    def close(self,):
        self._con.close()
