#!/usr/bin/python3

import os
import re
import sys
import bz2
import math
import shutil
import sqlite3
import urllib.request

import xml.etree.ElementTree as et
from time import perf_counter as tpc
from bisect import bisect_left

from sd.common import rns, sig, rint, percent
from sd.columns import auto_columns

import storage
from languages import CACHE
from letters import eprint, make_spellings
from storage import dump_json, load_json, loading, print_elapsed, open_any


def strip_tags(text):
	# print("debug stripping", text)
	tree = et.fromstring(text)
	return et.tostring(tree, encoding='utf8', method='text').decode()


def download_wiktionary():
	url = "https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2"
	filename = url.split("/")[-1]

	def progress(block_num, block_size, total_size):
		downloaded = block_num * block_size
		percent = downloaded / total_size * 100 if total_size > 0 else 0
		end_char = "\r" if downloaded < total_size else "\n"
		print(f"Downloading: {percent:6.2f}% ({downloaded/1024/1024:8.2f} MB / {total_size/1024/1024:8.2f} MB)", end=end_char, flush=True)

	response = input("Download enwiktionary dump? (y/n): ").strip().lower()

	if not response.startswith("y"):
		print("Exiting.")
		sys.exit(0)

	print("Starting download...")

	try:
		urllib.request.urlretrieve(url, filename, reporthook=progress)
		print(f"Download complete: {filename}")
	except Exception as e:
		print(f"Download failed: {e}")
		sys.exit(1)
		



def get_wiktionary_filename():
	# Find best bz2 file to read
	matches = []
	for filename in os.listdir('.'):
		if re.match('^..wiktionary-.*multistream.xml.bz2', filename):
			matches.append(filename)
	if not matches:
		eprint("Please place a wiktionary dump with a filename similar to:")
		eprint("\tenwiktionary-20230601-pages-articles-multistream.xml.bz2 in the same directory as the program file.")
		eprint("You can download it from this link:\n\thttps://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2") # pylint: disable=line-too-long
		
		if 'wordtree.py' in os.listdir('.'):
			download_wiktionary()
			return(get_wiktionary_filename())
		
		sys.exit(1)
	matches.sort()
	
	
	# Verify bz2 file
	for filename in matches:
		if os.path.getsize(filename) < 1e9:
			eprint(filename, "is too small.")
			eprint("I expected something larger than a gigabyte in size.")
			continue

		eprint("\nVerifying bz2 file:", filename)
		try:
			with bz2.open(filename, 'rb') as f:
				chunk_size = 100 * 1024**2
				total_read = 0
				for chunk in iter(lambda: f.read(chunk_size), b''):
					total_read += chunk_size
					print(f"Verified: {total_read//1024**2} MB", end='\r', flush=True)
		except Exception as e:
			eprint(f"Error during decompression: {e}")
			continue
		return filename
			
	eprint("No viable wiktionary bz2 file found.")
	sys.exit(1)


# print('Found file:', get_wiktionary_filename()); sys.exit()	# testing


def make_freq_table(filename, show_odds=True, extended=False):
	'''
	Scan through frequency list and return words fpm
	show_odds will show the chance of encountering a word if you learn at least a certain fpm
		enabling adds a few hundredths of a second of load time
	'''	
	
	start = loading("frequency table")
	
	
	# Optionally load prexisting json frequency tables
	if filename.lower().endswith('.json'):
		freq_table = load_json(filename)
		if '__TOTAL__' not in freq_table:
			eprint("No __TOTAL__ in json file. Attempting to calculate...")
			total = 0
			for val in freq_table.values():
				total += val
			freq_table['__TOTAL__'] = total
		return freq_table, freq_table['__TOTAL__']
	
	
	f = open_any(filename)
		
	total_count = 0
	sums = []			# The sum of hits in the table at each word line
	counts = []			# The raw hits at each word line
	freq_table = dict()
	for line in f:
		line = line.strip().split()
		if len(line) >= 2:
			word = line[0]
			if word.startswith('#'):
				continue
			try:
				count = int(line[1].replace(',', ''))
			except (ValueError, IndexError) as e:
				eprint("Invalid line!", line, '\n', e)
				continue
			# total_count += count
			freq_table[word] = count
			if show_odds:
				# sums.append(total_count)
				counts.append(count)
				
	f.close()
	print_elapsed(start)	
	
	# Sort counts Top to bottom and sum them up
	# Doing it this way allows for non sorted frequency files
	# only adds 0.01 seconds max
	counts.sort(reverse=True)
	for count in counts:
		total_count += count
		sums.append(total_count)


	eprint("\tThis table was created by scanning at least", rns(total_count), 'words of text.')
	eprint("\tFound", rns(len(freq_table)), 'unique words in frequency table.')
	# eprint("\t1 fpm is equivalent to", rns(total_count*1e-6), 'hits in this table.')
	

		
	if show_odds and total_count:		


		'''
		# Print percentage of the table targets
		print("Below are some estimates of how many words you need to learn to have a percentage chance of understanding a given word in a sentence. This is inaccurate because it includes every verb form, while you only have to learn the root word (lemma)")
		for goal in (70, 80, 90, 95, 99):
			target = bisect_left(sums, total_count * (goal / 100))
			print("\tLearning", rns(target), 'words will give you', str(goal) + '%')
		'''

		# Print fpm targets
		counts.reverse()					# Neccesary for bisect_left
		word_count = len(freq_table)
		# print('\n\nTotal hits =', rns(total_count))
		# print("Total words =", rns(word_count))
	

		if extended:
			fpms = []
			for base in (10, 1, .1, 0.01):
				fpms.extend([mult * base for mult in [10, 5, 2]])
			fpms.append(base)
		else:
			fpms = (10, 1, 0.1)	
		
		for fpm in fpms:
			# Convert desired fpm to raw hits
			target = fpm * 1e-6 * total_count
			
			# Find the index in the frequency table where this number of hits exists
			index = word_count - bisect_left(counts, target) - 1
			
			# Sum up the hits of all words before that index and divide by total hits
			fraction = sums[index] / total_count
			
			# print(fpm, 'fpm is equivalent to', rns(target), 'hits in this table')
			# print("\tFound at index", rns(index), '=', fraction)
			eprint('\tLearning every word higher than', show_fpm(fpm), 'will let you understand', \
			percent(fraction, 3 if fraction >= 0.95 else 2), 'of what you hear.') #, '(' + rns(target) + ')')
			if fraction >= 0.9995:			# Will show as 100%
				break

	return freq_table, total_count


def create_index(cur, con):
	# Indexes are a good thing
	if not cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_word'").fetchone():
		eprint("Building sql index...")
		cur.execute("CREATE INDEX idx_word ON words (word)")
		con.commit()


def make_data_base(dbname):
	if os.path.exists(dbname):
		assert dbname.endswith('.db')
		assert "wiktionary.words" in dbname
		os.remove(dbname)

	# Create database
	con = sqlite3.connect(dbname)
	cur = con.cursor()

	cur.execute("CREATE TABLE words(word, entry)")
	con.commit()
	con.close()



def make_word_tree(roots):
	'''Go through entire dictionary and build table of root words and all of their conjugations'''
	wt = dict()			# wordtree of: word->subs
	reverse = dict()	# Reverse tree of sub->final root
	index = 0


	def recurse(rword, seen=None, level=0):
		'''
		Recurse into the tags of each word
		Build up a line of words in seen until it reaches it's final root and dumps.
		'''

		for pair in roots.get(rword, []):

			root, tag = pair
			chain = (rword, tag, root)		# How a single word links to a root

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

	eprint("\n")
	for word in roots.keys():
		index += 1
		if not index % 10000:
			eprint("Building word tree:", rns(index), word)
		recurse(word)

	# Convert sets back to lists for storage
	for word in wt:
		wt[word] = list(wt[word])

	return wt, reverse


def fmt_fpm(fpm, digits=1):
	# print('debug fmt_fpm', digits, fpm)
	if digits < 1:
		return int(fpm)
	if fpm == 0:
		return 0

	if fpm >= 10:
		return int(fpm)
	elif fpm >= 1:
		return sig(fpm, digits=digits+2, trailing=True)
	else:
		return sig(fpm, digits=digits+1, trailing=True)
		


def show_fpm(fpm):
	return (sig(fpm, digits=2) if fpm >= 0.1 else sig(fpm, digits=1)) + ' fpm'


def display_digits(total):
	if not total:
		return 3 
	for digits in range(0,9):
		if 10**(-digits) < total / 10:
			break
	return digits
			

class Tree:
	'''Load database and word tree derived from wiktionary'''

	def __init__(self, freq_file, lang, debug=False):
		overall_start = tpc()

		self.debug = debug
		self.langcode = lang[0].lower()
		self.language = lang[1].title()
		self.cache = os.path.join(CACHE, self.langcode)
		os.makedirs(self.cache, exist_ok=True)

		dbname = os.path.join(self.cache, 'wiktionary.words.db')
		self.word_tree, self.reverse_tree = self.get_word_tree(dbname)

		# Can't be threaded because of large data size
		if not self.load_table(freq_file):
			sys.exit(1)

		start = loading("wikitionary database")
		self._con = sqlite3.connect(dbname)
		self._cur = self._con.cursor()
		
			
		self.words = {word[0] for word in self._cur.execute("SELECT word FROM words").fetchall()}
		
		print_elapsed(start)
		create_index(self._cur, self._con)		# Create index if it wasn't created by earlier versions



		spelling_file = os.path.join(self.cache, 'spelling.json')
		if not os.path.exists(spelling_file):
			self.spellings = make_spellings(self.words)
			dump_json(spelling_file, self.spellings)
		start = loading("spelling tree")
		self.spellings = load_json(spelling_file)	# Seems to be faster directly

		print_elapsed(start)
		eprint("Loaded wiktionary database with", rns(len(self.words)), 'words available.')
		if tpc() - overall_start < 60:
			eprint("Total tree class loading time:", rns(tpc() - overall_start), 'seconds')


	def load_table(self, freq_file, **kargs):
		if not os.path.exists(freq_file):
			eprint("Error:", freq_file, "does not exist.")
			return False
		freq, total = make_freq_table(freq_file, **kargs)
		if freq and len(freq) >= 10:
			self.freq, self.freq_total = freq, total
			return True
		eprint("Error: frequency table not loaded.")
		return False


	def check_spelling(self, word):
		'''Try to match a word without accents'''
		if word in self.words:
			return word
		if word in self.spellings:
			cans = self.spellings[word]
			if len(cans) != 1:
				eprint("\nDid you mean to type:", ' or '.join(cans), '?')
				cans = {self.get_fpm(word):word for word in cans}
				word = cans[sorted(cans.keys())[-1]]
				eprint("Returning the most common word:", word)
				return word
			eprint("\nCorrecting word:", word, 'to', cans[0])
			return cans[0]
		return word


	def root_entry(self, entry):
		"Scan dictionary entry looking for roots and tags"
		root = None			# Discovered root of word
		tags = []			# Pairs of (root word, tag (like 'es-verb form of')

		# Skip certain troublesome wiki sections
		section = ''			# Current Wiki Section
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
				code = list(filter(None, code)) 			# Filter blanks in list
				if not code:
					eprint('Malformed line in text:', line)
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
							eprint('Cannot process:', code)
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
			"Write buffer of entries to database"
			cur.executemany("insert into words (word, entry) values (?, ?)", out)
			con.commit()


		def add_word():
			"Process a word and its entry."
			if entry:
				word = strip_tags(title_line).replace('[', '').replace(']', '')
				if ':' in word:
					# Example: https://en.wiktionary.org/wiki/Module:en-headword
					if debug_flag >= 4:
						eprint("Skipping:", word)
				else:
					if word in all_words:
						eprint("Overwriting:", word)
					else:
						all_words.add(word)

					# Append entry to buffer
					out.append((word, '\n'.join(entry)))

					# Process tags from entry
					tags = self.root_entry(entry)
					if tags:
						root_dict[word] = tags

		eprint("Building word database in", dbname)
		eprint("Reading from file:", wiktionary_file)
		expected = 200 * (os.path.getsize(wiktionary_file) / 1000)		# Lines per KB
		eprint("\nThere should be around", rns(round(expected * 0.8, -7)), 'to', rns(round(expected * 1.2, -7)), \
		"lines of xml text to process.")		# Rounded to the nearest 10 million lines
		eprint("Please wait a few minutes... You will only have to do this once per language:\n")


		progress = 0 				# Track progress in file
		update_rate = 10**6			# How often to display progress txt
		root_dict = dict()			# word -> root_entry(word)
		title_line = ""				# Line of xml starting with <title>
		entry = []					# Entry for a noun
		all_words = set()			# Set of all words
		out = []					# Output ready to be synced with database

		sec_flag = False			# Start of requested language section in each entry
		sec_search = '==' + self.language + '=='

		debug_flag = self.debug		# For debugging
		debug_history = []			# Full list of lines between <title> without processing
		rep_flag = False			# Repeated language section


		# Read the bz2 file and process into sqlite database
		# Note: for testing use: pv enwiktionary* | pbzip2 -d | grep -B1000 -A100 "search term"
		with bz2.open(wiktionary_file) as f:
			for progress, line in enumerate(f):
				if not progress % update_rate:
					if progress == 0:
						start = tpc()		# Start time is more accurate if it reads a line first to get things going
					elif (debug_flag and (progress == 4 * update_rate or not progress % (update_rate * 100))) or \
					not debug_flag:
						eprint('Read', rns(progress), 'lines at a rate of', rns(progress / (tpc() - start)), \
						'lines per second.', 'Found', rns(len(all_words)), 'entries so far...')
				if debug_flag:
					debug_history.append(line)

				line = line.decode().strip()
				if line.startswith("<comment>"):
					# Eliminates all of the Repeated language sections
					continue

				# Look for title line to mark the start of a new entry
				if line.startswith("<title>"):
					# Debug: show repeated entry
					if debug_flag:
						if rep_flag:
							rep_flag = False
							for l in debug_history[:-1]:
								eprint(l)
							eprint("\n"*3)
						debug_history = [debug_history[-1]]		# Reset debug_history

					sec_flag = False	# Sections only apply to the current entry
					add_word()		# If a new title line is reached, then pull word and entry from the last section
					# Sync with database every so many entries
					if len(out) >= 1e5:
						commit()
						out = []

					entry = []				# Clear the entry to get read for the new one
					title_line = line		# From the last line read title

				# Only add requested language section to entry
				if sec_flag:
					if line.count('==') == 2 and '===' not in line:
						# testing code: if '==' in line: did not improve speed
						if sec_search in line and ':' not in title_line:
							# This shouldn't happen. It indicates a repeated language section like in
							# the code for chavomadurismo
							if self.debug:
								eprint("Repeated language section:", title_line)
								rep_flag = True
						else:
							sec_flag = False
					else:
						if not line.startswith('<'):
							entry.append(line)
						'''
						elif not ':' in title_line:
							# This shouldn't happen and when it does it's 100% nonsense
							for s in ('sha1 revision page'.split()):
								if s in line:
									break
							else:
								eprint('<<<< ', line)
						'''

				elif sec_search in line:
					# Must be "in" line because some sections start with xml tags
					sec_flag = True

		add_word()		# Don't forget that final entry
		commit()

		eprint("Read", f"{progress + 1:,}", "lines in", rns((tpc() - start) / 60), 'minutes')
		eprint("Averaged", rint(progress / (os.path.getsize(wiktionary_file) / 1000)), 'lines per KB')
		
		create_index(cur, con)
		con.close()

		return root_dict


	def get_word_tree(self, dbname):
		#  Cache Files
		meta_file = os.path.join(self.cache, 'meta.json')
		tree_file = os.path.join(self.cache, 'tree.json')
		roots_file = os.path.join(self.cache, 'roots.json')
		reverse_file = os.path.join(self.cache, 'reverse.json')


		# The meta file stores current state
		if os.path.exists(meta_file) and self.debug < 3:
			meta = load_json(meta_file)

		else:
			meta = dict(words_finished=False, tree_finished=False)


		# Create sqlite database for words from wiktionary
		if not meta['words_finished']:

			# Current "en" folder is 751 MB so I'm setting a minimum HDD space of a gig
			if shutil.disk_usage(self.cache).free < 1e9:
				eprint("You should probably clear up some hard drive space before running this.")
				sys.exit(1)

			eprint("\nThe current language is set to:", self.langcode, self.language)
			eprint("You can change this by running the program with a different --lang setting.")
			eprint("Use --help for more info.\n")

			make_data_base(dbname)
			roots = self.make_all_words(dbname)

			# Save roots to file
			dump_json(roots_file, roots)
			meta['words_finished'] = True
			dump_json(meta_file, meta)


		# Make the word tree associating words and roots
		if not meta['tree_finished']:
			roots = load_json(roots_file)
			word_tree, reverse_tree = make_word_tree(roots)

			if word_tree:
				# todo write tree_file directly to csv directly after testing
				eprint("Writing word tree to .json")
				dump_json(tree_file, word_tree)
				eprint("Writing reverse word tree to .json")
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
					eprint('\nFound root of', word, '->', ', '.join(roots))
				if len(roots) == 1:
					return roots[0]
				if not silent:
					eprint('\nMultiple possible roots:')
				out = []
				for root in roots:
					fpm = self.get_fpm(root)
					out.append((fpm, root))
					if not silent:
						eprint(fmt_fpm(fpm), root)

				out.sort()
				root = out[-1][1]
				if not silent:
					eprint('Chose root:', root)
				return root
		return None


	def get_fpm(self, word):
		hits = self.freq.get(word, 0)
		return hits / self.freq_total * 1e6


	def get_entry(self, word):
		if word in self.words:
			if '"' in word:
				return "Skipping entry for " + word
			entry = self._cur.execute('select entry from words where word=' + '"' + word + '"').fetchone()
			if entry:
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
			eprint("Baseline =", show_fpm(baseline))

		return baseline


	def total_freq(self, word, args, branch=None, silent=False):
		book = args.book
		nostars = not args.stars
		highstars=args.starval
	
		"Look up any word and return fpm of all conjugations combined."
		root = self.find_root(word, silent=True) or word

		book_total = 0		# Words in book
		high_total = 0		# Total of words with *
		high_book = 0		# Words in book that are listed with *

		subs = self.word_tree.get(root, []).copy()
		subs.append((root, '', ''))
		subs.sort()
		found = dict()		# dict of subs to be used in output


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
			if args.bookfpm:
				out[0].insert(3, 'BFPM:')


		# Choose which subs to include and count up totals
		for sub, tag, subroot in subs:
			def add_sub():
				nonlocal total_hits, high_total, high_book
				if sub in found:
					return
				total_hits += hits		
				# The original root gets an R, unsually common words get a * for further review
				high = 'R' if sub == root else ''
				if not high:
					if hits / baseline >= highstars:
						high_total += hits
						high_book  += bc
						high = '*' * int(math.log((hits / baseline) / highstars, 2))		
				found[sub] = dict(tag=tag, subroot=subroot, high=high)

		
			#Add up hits if it's a new sub
			hits = all_hits[sub]
			if sub not in found:
				bc = book.get(sub, 0) if book else 0		# book count of sub
				if branch:
					# Match only words with tag linking back to branch
					if subroot == branch or sub == branch:	# pylint:disable=consider-using-in
						add_sub()
					else:
						continue						
			add_sub()
		
		
		#for sub, info in found.items():
		#	print(sub, info)
					



		# Show everything if not many skipped lines, else print lines above threshold
		skipped = 0			# Number of words with hits below threshold
		# Make output
		last = ''
		digits = display_digits(total_hits)
		if args.showall:
			threshold = -1
			digits += 2
		else:
			threshold = 10**(-digits) if total_hits > 0 else 0.001
		
		for sub, info in found.items():
			tag = ' '.join((info['tag'], info['subroot'])).strip()
			
			if sub == last:
				# If the same sub has multiple tags:
				if tag:
					if book:
						if args.bookfpm:
							out.append(('', '', '', '', '', tag))
						else:
							out.append(('', '', '', '', tag))
					else:
						out.append(('', '', '', tag))
			else:
				last = sub		
				hits = all_hits[sub]
				
				# Don't show subs below threshold
				if hits < threshold and sub != root and sub != word:
					skipped += 1
					continue

					
				bc = book.get(sub, 0) if book else 0	
				book_total += bc	
				#
				line = [sub, fmt_fpm(hits, digits=digits), info['high'], tag]
				if book:
					line.insert(2, fmt_fpm(bc) or '')
					if args.bookfpm:
						line.insert(3, fmt_fpm(bc / book['__TOTAL__'] * 1e6, digits) or '') # also show book fpm
				out.append(line)		
	
	
		# nostars mode removes * words from total
		if nostars:
			total_hits -= high_total
			book_total -= high_book		
	
		if not silent:
			auto_columns(out, space=2, printme=True)
			if skipped:
				print("(skipped showing", skipped, f'conjugations below threshold of {threshold} \n')
			if high_total:
				if nostars:
					print("Total with stars words would have been:", fmt_fpm(total_hits + high_total), 'fpm')
				else:
					print("(total without abnormally high * words is", str(fmt_fpm(total_hits - high_total)) + ')')

					
		return total_hits, book_total




	def close(self,):
		self._con.close()
