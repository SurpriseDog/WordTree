#!/usr/bin/python3

# Scan database for spanish gender words that don't match.
# Assumes existing run of ./wordtree.py

# Usage: ./gender.py

import os
import re
import sys
import sqlite3
from time import perf_counter as tpc

from sd.common import undent
from sd.common import rns, percent
from sd.easy_args import easy_parse
from sd.columns import auto_columns
from tree import make_freq_table, fmt_fpm, loading, print_elapsed


IS_WINDOWS = bool(os.name == 'nt')
if IS_WINDOWS and sys.flags.utf8_mode == 0:
    print("Windows users must run this program with: python3 -X utf8")
    sys.exit(1)


def eprint(*args, **kargs):
    print(*args, file=sys.stderr, **kargs)


def parse_args():
    "Parse arguments"

    optionals = [\
    ['ending', '', str, ''],
    '''Limit nouns to only those ending in these letters.
    --ending ma will just show all of them as there is no consistent rule.
    ''',
    ['min', '', float, 0.1],
    "Minimum fpm to show a word.",
    ['max', '', float, 0],
    "Maximum fpm to show a word.",
    ['length', '', int, 0],
    "Screen out nouns under this length.\nFor example 'la te' is technically a noun meaning the letter t.",
    ['lang', '', str, 'es'],
    "2 digit language code.",
    ['sm', '', list, ('l', 'o', 'n', 'e', 'r', 's')],
    "Male suffix list",
    ['sf', '', list, ('d', 'ion', 'ión', 'z', 'a')],
    "Female suffix list",
    ['su', '', list, ('ma',)],
    "Unknown suffix list",
    ]


    description = '''
    Scan the wiktionary database for nouns
    that don't follow the L-O-N-E-R-S or D-IÓN-Z-A rules.
    You must first run ./wordtree.py first to build the database.
    '''

    args = easy_parse(optionals, usage='./gender.py', description=undent(description.strip()))

    return args




def suffix_gender(word, suffix_m, suffix_f, suffix_u):
    "Get gender of word based on suffixes."
    if ' ' in word:
        return '?'

    '''
    if word.endswith(suffix_u):
        return '?'
    if word.endswith(suffix_f):
        return 'f'
    elif word.endswith(suffix_m):
        return 'm'
    return '?'
    '''

    # Step through the arrays u, f, m in turn until a suffix is found or all arrays exhausted
    i = -1          # index
    while True:
        i += 1
        suffix = ''     # word ending
        for gender in range(3):
            array = (suffix_u, suffix_f, suffix_m)[gender]
            if i < len(array):
                suffix = array[i]
                # print('debug', i, gender, suffix)
                if word.endswith(suffix):
                    return ('?', 'f', 'm')[gender]
        if not suffix:
            # Suffix lists exhausted, reset
            # print('reset'); input()
            return '?'



def process_entry(entry, lang):
    "Get the gender from a wiktionary entry."
    search_term = lang + '-noun'


    for line in entry:
        line = line.lower().strip()

        for code in re.findall('{{[^{]*}}', line):
            # print("Section:", section, "Tag:", code)

            code = code.lower().strip('{{}}').split('|')
            code = list(filter(None, code))             # Filter blanks in list
            if not code:
                print('Malformed line:', line)
                continue
            tag = code[0]
            if search_term in tag:
                gender = code[1].replace('bysense', '')
                # print(tag, gender, line)
                return gender
    return ''


'''
def tag_gender(tag):
    #Get gender for wikitags
    gender = re.search('.*es-noun|([^|]*).*}}', tag)
    if not gender:
        return ''
    gender = gender.group(1)
    return gender
'''

def loader(lang):
    "Load words and entries into memory."
    dbname = os.path.join('cache', lang, 'wiktionary.words.db')
    freq_file = os.path.join('freq', lang + '.xz')

    if not all(map(os.path.exists, (dbname, freq_file))):
        print("Missing cache files. Run wordtree.py on target language first.")
        return None, None, None

    start = loading("frequency table")
    freq_table, total_hits = make_freq_table(freq_file)
    freq_table = sorted(freq_table.items(), key=lambda item: item[1], reverse=True)
    print_elapsed(start)


    start = loading("database")
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    data = dict(cur.execute("SELECT word, entry FROM words").fetchall())
    con.close()
    print_elapsed(start)
    return data, freq_table, total_hits


def fix_gender(word, gender):
    if '=' in gender:
        fixed = re.sub(r'[^A-Za-z]', '', gender)
        if len(fixed) == 1:
            eprint("Fixed malformed gender:", word, gender, '->', fixed)
            gender = fixed
    return gender


class TriGender:

    def __init__(self, args):
        '''Generate the list of gender suffixes to try and their
        associated genders'''

        i = -1
        self.suffixes = []
        self.genders = []

        while True:
            i += 1
            suffix = ''     # word ending
            for gender in range(3):
                array = (args.su, args.sf, args.sm)[gender]
                if i < len(array):
                    suffix = array[i]
                    self.suffixes.append(suffix)
                    self.genders.append(('?', 'f', 'm')[gender])
            if not suffix:
                break
        eprint("Trying suffixes in order:", ", ".join(self.suffixes))
        # eprint(self.genders)


    def classify(self, word):
        for index, suffix in enumerate(self.suffixes):
            if word.endswith(suffix):
                gender = self.genders[index]
                # print(word, suffix, gender)
                return gender
        return '?'




def main():
    "Find spanish nouns where gender doesn't follow the rules."
    args = parse_args()
    os.chdir(sys.path[0])       # change to local dir
    data, freq_table, total_hits = loader(args.lang)
    if not data:
        return False

    wp = 0          # Words processed
    found = 0       # total nouns found
    rogues = 0      # rogues found

    '''
    suffix_m = tuple(args.sm)
    suffix_f = tuple(args.sf)
    suffix_u = tuple(args.su)
    '''
    tg = TriGender(args)


    start = tpc()
    out = [['FPM:', 'Word:', 'Gender:']]
    for word, hits in freq_table:
        if word not in data:
            continue

        fpm = hits / total_hits * 1e6
        if fpm < args.min:
            break
        if args.max and fpm > args.max:
            continue
        if args.ending and not word.endswith(args.ending):
            continue

        if word in data:
            if len(word) < args.length:
                continue
            entry = data[word].split('\n')
            wp += 1
            gender = process_entry(entry, args.lang)
            if gender:
                # Is a noun
                if 'p' in gender:
                    # No plurals
                    continue

                found += 1
                if gender in ('?', 'mf'):
                    # skip words we can't determine gender of
                    continue
                if len(gender) != 1:
                    gender = fix_gender(word, gender)
                if len(gender) != 1:
                    eprint("Skipped malformed gender:", word, gender)
                    continue

                if word.endswith('ma'):
                    assumed = '?'
                else:
                    # assumed = suffix_gender(word, suffix_m, suffix_f, suffix_u)
                    assumed = tg.classify(word)
                    # print(word, assumed)
                    if assumed == '?':
                        continue
                if (assumed != gender and assumed != '?') or \
                    (args.ending == 'ma' and word.endswith('ma')):
                    fpm = rns(fpm, digits=2) if fpm < 10 else int(fpm)
                    out.append((fpm, word, ' '.join((assumed, '->', gender))))
                    rogues += 1


    eprint("Processed", rns(wp), "words in", rns(tpc() - start, digits=2), 'seconds')
    eprint("\n"*3)
    auto_columns(out, space=2, printme=True)
    if args.ending == 'ma':
        print("\nFound", rns(found), 'nouns')
    else:
        print("\nFound", rns(found), 'nouns of which', percent(rogues / found, digits=2), 'were rogues')
    return True

if __name__ == "__main__":
    sys.exit(not main())
