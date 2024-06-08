#!/usr/bin/python3

# Scan database for spanish gender words that don't match.
# Assumes existing run of ./wordtree.py

# Usage: ./gender.py

import os
import re
import sys
import sqlite3
from time import perf_counter as tpc

from sd.common import rns, percent
from sd.easy_args import easy_parse
from sd.columns import auto_columns, undent
from tree import make_freq_table, fmt_fpm, loading, print_elapsed


M_SUFFIXES = ('l', 'o', 'n', 'e', 'r', 's')
F_SUFFIXES = ('d', 'ion', 'ión', 'z', 'a')


def parse_args():
	"Parse arguments"

	optionals = [\
	['ending', '', str, ''],
	'''Limit nouns to only those ending in these letters.
	--ending ma will just show all of them as there is no consistent rule.
	''',
	['min', '', int, 1],
	"Minimum fpm to show a word.",
	['max', '', int, 0],
	"Maximum fpm to show a word.",
	['length', '', int, 3],
	"Screen out nouns under this length.\nFor example 'la te' is technically a noun meaning the letter t.",
	]

	description = '''
	Scan the wiktionary database for nouns
	that don't follow the LONERS or D-ION-Z-A rules.
	You must first run ./wordtree.py first to build the database.
	'''

	args = easy_parse(optionals, usage='./gender.py', description=undent(description.strip()))

	return args




def suffix_gender(word):
	"Get gender of word based on suffixes."
	if ' ' in word:
		return '?'
	if word.endswith('ma'):
		return '?'
	if word.endswith(F_SUFFIXES):
		return 'f'
	elif word.endswith(M_SUFFIXES):
		return 'm'
	return '?'


def process_entry(entry):
	"Get the gender from a wiktionary entry."

	for line in entry:
		line = line.lower().strip()

		for code in re.findall('{{[^{]*}}', line):
			# print("Section:", section, "Tag:", code)

			code = code.lower().strip('{{}}').split('|')
			code = list(filter(None, code)) 			# Filter blanks in list
			if not code:
				print('Malformed line:', line)
				continue
			tag = code[0]
			if 'es-noun' in tag:
				gender = code[1].replace('bysense', '')
				# print(tag, gender, line)
				return gender
	return ''



def tag_gender(tag):
	'''Get gender for wikitags'''
	gender = re.search('.*es-noun|([^|]*).*}}', tag)
	if not gender:
		#print("Error getting gender of:", word, line)
		return ''
	gender = gender.group(1)
	return gender


def loader():
	"Load words and entries into memory."
	dbname = 'cache/es/wiktionary.words.db'
	freq_file = 'freq/es.xz'

	if not all(map(os.path.exists, (dbname, freq_file))):
		print("Missing files. Run ./wordtree.py first")
		return None, None, None

	start = loading("frequency table")
	freq_table, total_hits = make_freq_table(freq_file)
	freq_table = sorted(freq_table.items(), key=lambda item: item[1], reverse=True)
	print_elapsed(start)


	start = loading("database")
	con = sqlite3.connect(dbname)
	cur = con.cursor()
	# data = {word:entry for word, entry in cur.execute("SELECT word, entry FROM words").fetchall()}
	data = dict(cur.execute("SELECT word, entry FROM words").fetchall())
	con.close()
	print_elapsed(start)
	return data, freq_table, total_hits


def fix_gender(word, gender):
	if '=' in gender:
		fixed = re.sub(r'[^A-Za-z]', '', gender)
		if len(fixed) == 1:
			print("Fixed malformed gender:", word, gender, '->', fixed)
			gender = fixed
	return gender


def main():
	"Find spanish nouns where gender doesn't follow the rules."
	args = parse_args()
	data, freq_table, total_hits = loader()
	if not data:
		return False

	wp = 0			# Words processed
	found = 0		# total nouns found
	rogues = 0		# rogues found

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
			if len(word) < args.min:
				continue
			entry = data[word].split('\n')
			wp += 1
			gender = process_entry(entry)
			if gender:
				# Is a noun
				found += 1
				if 'p' in gender:
					# No plurals
					continue

				if gender in ('?', 'mf'):
					# skip words we can't determine gender of
					continue
				if len(gender) != 1:
					gender = fix_gender(word, gender)
				if len(gender) != 1:
					print("Skipped malformed gender:", word, gender)
					continue

				if word.endswith('ma'):
					assumed = '?'
				else:
					assumed = suffix_gender(word)
					if assumed == '?':
						continue
				if assumed != gender:
					out.append((fmt_fpm(fpm), word, ' '.join((assumed, '->', gender))))
					rogues += 1

	# print_elapsed(start)
	print("Processed", rns(wp), "words in", rns(tpc() - start, digits=2), 'seconds')
	print("\n"*3)
	auto_columns(out, space=2, printme=True)
	print("\nFound", rns(found), 'nouns of which', percent(rogues / found), 'where rogues')
	return True

if __name__ == "__main__":
	sys.exit(not main())
