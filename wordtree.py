#!/usr/bin/python3

import os
import re
import sys
import csv
import time

from bisect import bisect_right
from time import perf_counter as tpc


import myanki
import mybook
from sd.common import rns
from manual import manual_input
from sd.columns import auto_columns
from languages import LANGCODES, CACHE
from letters import strip_punct, eprint
from word import Word, log_weighted_avg
from args import parse_args
from storage import make_or_load_json, dump_json
from tree import Tree, fmt_fpm, loading, show_fpm

	
def show_version():
	eprint("\nWordTree version: 1.20.0")
	# Version History:
	# 1.1 New --lang features 
	# 1.2 Added option a in manual mode to show all conjugations
		# minor fixes
	# 1.3 Radically increased word definition lookup speed from 20 to 10K per second
	# 1.4 Can now correct partial lang names to full. 
		# Example: --lang hung autocorrects to Hungarian
		# Infinite history. Just keep pressing down
	# 1.5 Show odds of encountering a word irl if you learn at least a certain fpm range
	# 1.6 Print and edit the history for easy saving
	# 1.7 Fix ranking system
	# 1.8 You can now check duplicates against a list in manual mode with --dupes
	# 1.9 New cmd options
	# 1.10 RAE corpus support
	# 1.11 Load a frequency list in the book fpm slot
	# 1.12 clean_wikitext function
	# 1.20 Major Refactor. Added test suite.


def read_clippings(filename, skiplines=0):
	"Detect My Clippings format and return words if true."
	kindle = 0		# Count of lines like kindle format
	count = 0		# Count of all lines
	prev = ''		# Previous line
	prev2 = ''		# 2 lines back
	words = []		# list of words collected

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
					kindle += 0.5			# a single word on a line before ===== only suggests kindle format
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



def get_words(filename, short_len, skiplines=0, multiline=-1):
	'''Read csv, txt or kindle clippings.txt
	multiline = 1 # True: Read many words per line
	multiline = 0 # False: Read one word per line
	multiline = -1 # Autodetect
	'''
	words = []
	book_mode = False			# Read multiple words per line
	short_words = set()

	def add_word(word):
		'''add word to table'''
		nonlocal words
		if word and not word.startswith('#'):
			word = strip_punct(word).lower()
			if not word.strip():
				pass
			elif not book_mode and len(word) <= short_len:
				# print('Skipping short word:', word)
				short_words.add(word)
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

		elif multiline >= 1 or (multiline == -1 and mybook.detect_book(filename)):
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
	
	if short_words:
		eprint("Short words skipped in input file:", ' '.join(sorted(list(short_words))))
	# eprint("Found:", len(words), "unique words")
	return words


def load_anki(args):
	'''
	Get existing anki cards and make a searchable dict of Question words->Matching Notes
	'''
	anki = dict()
	loading("anki database", newline=True)
	notes = myanki.getnotes(args.anki)
	eprint("\tFound", rns(len(notes)), 'notes.')
	decks = tuple(args.decks)	# Which deck's words to include.
	limit = args.ankilimit		# Number of words to search at start of card
	count = 0

	for nid, note in notes.items():
		if decks and note['deck'].startswith(decks):
			continue
		q = re.sub('<[^<]+>', ' ', note['question'])		# try to strip out any xml tags
		q = q.replace('&nbsp;', ' ').lower()			# These tags are the bane of my existence
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

	filename = os.path.join(CACHE, 'usage.json')
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
		with open('reviews.txt') as f:
			print(f.read())

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



def output_csv(ranked, ofile, book_freq):
	'''Ouput words as csv file.'''
	if not book_freq:
		book_freq = dict()
	with open(ofile, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		if book_freq:
			writer.writerow("Word Root FPM Total_FPM Book_Count Book_FPM Ratio".split())
			for word in ranked:
				ratio = round(word.book_fpm / word.fpm,1) if word.fpm else 0
				writer.writerow([word.word, word.root, fmt_fpm(word.fpm), fmt_fpm(word.derived), word.book_count, word.book_fpm, ratio])
		else:
			writer.writerow("Word Root FPM Total_FPM".split())
			for word in ranked:
				writer.writerow([word.word, word.root, fmt_fpm(word.fpm)])
			
		

	eprint("Writing csv file:", ofile)
	return True


def find_dupes(words, tree, args):
	"Convert a list of raw words into word objects with dupe counts"
	unranked = dict()				# raw word->word object
	processed = 0
	if words:
		eprint("\nCalculating the frequency and root of every word in the list of", rns(len(words)))

	
	# Duplicate based on the raw word
	'''
	for word in words:
		if word in unranked:
			unranked[word].dupes += 1
		else:
			unranked[word] = Word(word, tree, args)
	return unranked
	'''
	
	# Duplicate based on the root word
	
	start = tpc()	
	for raw in words:
		processed += 1
		if not processed % 1000 and len(words) > 3000:
			if not processed % (1000 * 10) or processed < 1000 * 10:
				wps = int(processed / (tpc() - start))
				eprint("Processed", rns(processed), 'words at', rns(wps), 'per second:', word.word)
				
		word = Word(raw, tree, args)
		root = word.root
		if root in unranked:
			unranked[root].dupes += 1
			# print("Found dupe:", raw, root)
		else:
			unranked[root] = word
	return unranked
	
	
def sci(number):
	return "{:.1e}".format(number)
		
		
def rank_list(words, tree, args):
	"Rank the list of words and return Word objects"
	ranked = []		# words resorted by adj factor
	unranked = find_dupes(words, tree, args)
	
	
	# Sort words by adjusted value
	for word in unranked.values():
		if not word.skipped(args):			
			fpm = word.calc_adj(args)
			
			# apply sortfactor if valid
			adj = fpm
			if word.fpm:
				'''
				adj = (fpm / word.fpm) ** (args.sortfactor/100)
				# print('adj =', adj, word.fpm, fpm, word.fpm * adj, word.word)
				fpm = word.fpm * adj
				'''
				
				# example: a factor of 10 means the original fpm is weighted 1/10 toward the word fpm
				adj = log_weighted_avg(word.fpm, fpm, args.sortfactor/100)
				if word.fpm < 0.01:
					pass # print(percent(adj/fpm), word.word, sci(word.fpm), sci(fpm), sci(adj))
				
					
				#if word.dupes >= 2:
				#	print(word.dupes, word.word)
				# print(word.fpm, fpm, 'sort =', adj, '\n\n')
					
			ranked.append((adj, word))
			# print("Ranking", ranked[-1])
			
	if args.nosort:
		eprint("List was not sorted.")
	else:
		eprint("Sorting list...")
		ranked.sort(key=lambda x: x[0], reverse=not args.reverse)


	if args.stop:
		ranked = ranked[:int(args.stop)]
	if args.start:
		ranked = ranked[int(args.start):]
		


	if len(unranked) >= 100:
		fpms = []
		# sequence = [10**(1/4), 10**(2/4), 10**(3/4), 10]	# 10, 17, 31, 56
		# sequence = [10**(1/3), 10**(2/3), 10]				# 10, 21, 46, 100
		# sequence = [10**(1/2), 10]						# 10, 31, 100
		# sequence = [2, 5, 10]								# (looks better)
		# sequence = [2.1, 4.6, 10]							# more accurate
		sequence = [10,]
		eprint("\nFrequency table of input file:")
		for base in (100, 10, 1, .1, 0.01, 0.001):
			fpms.extend([mult * base for mult in reversed(sequence)])
		fpms.append(base)
		fpms.append(0)
		fpms.reverse()
		bins = [0] * len(fpms)
		for f, _ in ranked:
			b = bisect_right(fpms, f) - 1
			# eprint(f, b, fpms[b])
			bins[b] += 1
		
		for i, f in enumerate(fpms):
			text = show_fpm(f).replace('fpm', 'to')
			if i < len(fpms) - 1:
				text = text + ' ' + show_fpm(fpms[i+1])
			else:
				text = show_fpm(f) + '+'
			eprint(text.ljust(20), bins[i])		
		# eprint("\n\nPress Enter to see result:"); input()

	# Return the sorted list of words
	return [row[1] for row in ranked]
	

def cumulative_word_percentiles(word_count):
	if not word_count:
		return

	total_count = sum(count for _, count in word_count)

	cumulative = 0
	idx = 0
	
	eprint("\n\nWord percentiles found in text:\n")
	out = []
	for p in [75, 90, 95, 99]:
		threshold = (p / 100) * total_count

		# Move through the list until cumulative sum exceeds threshold
		while cumulative < threshold and idx < len(word_count):
			cumulative += word_count[idx][1]
			idx += 1

		# Get last words
		fpm = word_count[idx-1][0].derived
		fpm = show_fpm(fpm).ljust(10)
		for count in range(11, 0, -1):
			if idx + count >= len(word_count):
				continue
			last_words = ', '.join([w.word for w, _ in word_count[idx:idx+count]])
			if len(last_words) <= 64:
				break
		out.append(((f"{p}th percentile at " + fpm, last_words+'...')))
	auto_columns(out, space=0, printme=True, eprint=True)

	eprint("\nThis ignores 0 fpm words, which are usually punctuation errors, proper names and the like. The idea is that if you can understand the 75th percentile words (and easier), then you can understand 75% of the words on the page.")



def rank_book(args, tree):
	"Output table of entire book with word, occurences, fpm"


	eprint("\n")
	filename = args.rankbook or args.filename
	book = mybook.load_book(filename)

	total = book.pop('__TOTAL__')

	# Get words
	words = [[key, val] for key, val in book.items()]
	# words = [['carcajada', 7]]; total = 100; filename = 'test_out'
	
	if not words:
		eprint(r"Error. Could not find any words ¯\_(ツ)_/¯ ")
		return False
	words.sort(key=lambda x: x[1], reverse=True)
	
	eprint("Found", rns(len(words)), "unique words in book out of", rns(total), 'total words.\n')

	
	
	ranked = rank_list(words, tree, args)

	
	# Build percentile list
	out = []
	words = dict(words)
	for word in ranked:
		fpm = word.calc_adj(args)
		if not fpm:
			# print(word.word); continue
			break
		out.append((word, words[word.word]))

	if len(out) > 100:
		cumulative_word_percentiles(out)
	

	written = 0
	eprint("\n")
	
	
	if args.csv:
		ofile = args.csv
	else:
		ofile = os.path.basename(filename) + '.csv'
	
	with open(ofile, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		out = "Word Count Word_FPM Book_FPM Ratio Root Total_FPM Book_Total Ratio_Total".split()
		if not args.book:
			out = out[:-2]
		writer.writerow(out)

		for word in ranked:
			# print('debug rank_Book', word.word, word.skipped(args))
		
			if word.skipped(args):
				continue
			
			
			count = word.extra[0]
			book_fpm = count / total * 1e6
			
			# fpm ratio for lemma not total
			fpm_ratio = book_fpm / word.fpm if word.fpm else -1
			
			
			
			fpm_ratio = int(fpm_ratio) if fpm_ratio >= 10 else round(fpm_ratio, 2)	
			out = [word.word, count, word.fpm, fmt_fpm(book_fpm), fpm_ratio, word.root, word.derived]
	
	
			# A little confusing because the rank_book words and args.book 
			# are not neccesarily the same book			
			if args.book:
				_, book_total = tree.total_freq(word.word, args, branch=None, silent=True)
				book_total = book_total / args.book['__TOTAL__'] * 1e6
	
				# print('debug rank_book', word.word, word.root, word.derived, book_total)
				total_ratio = book_total / word.derived if word.derived else -1
				out.extend([book_total, total_ratio])		
		
			writer.writerow(out)
			written += 1


	eprint(rns(written), "words written to:", ofile)
	return True


def process_list(words, tree, args):
	"Process a list of words"
	# Cancel out a word in words for each word in ignore
	# Done before duplicates, because that will remove words
	if args.ignore:
		words = ignore_words(words, args.ignore)

	# Sort the words into a list of ranked Word objects
	ranked = rank_list(words, tree, args)

	if args.csv:
		return output_csv(ranked, args.csv, args.book)

	eprint("\n\nDone! Here are the words with definitions.")
	with open('warning.txt') as f:
		for line in f.readlines():
			eprint(line.strip() + '\n')
		

	eprint("Processing", len(ranked), "words...")
	start = tpc()
	
	
	# Output words and definitions
	if len(ranked) > 1000 and not args.noentry and args.wikiclean:
		eprint("\nWarning: --wikiclean is turned on which will slow your output.")
	
	
	for count, word in enumerate(ranked):
		if count and not count % 1000:
			eprint("Processing word:", rns(count), 'of', rns(len(ranked)))
		print('\n' * 5)
		word.print_info(tree, args)
		if not args.noentry:
			word.print_entry(tree, wikiclean=args.wikiclean)

	end = tpc()
	eprint("Finished in", rns((end - start)), 'seconds at a rate of', rns(len(ranked) / (end - start)), 'wps')
	return True


def main():
	args = parse_args()
	if args.debug:
		print(args)
	os.chdir(sys.path[0])		# change to local dir
	show_version()
	
	# Load data
	tree = Tree(args.freq, args.lang, debug=args.debug)
	args.anki = load_anki(args) if args.anki else dict()
	eprint("\n")


	if args.book:
		args.book = mybook.load_book(args.book)
	if args.rankbook:
		return rank_book(args, tree)


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
		words=[]
		if args.dupes:
			words = get_words(args.dupes, args.length, skiplines=args.skiplines, multiline=args.multiline)
			eprint("Found", len(words), "words in input file:", args.dupes)					
		eprint("No filename specified, but you can manually type in a word below if you wish:")
		return manual_input(tree, args, find_dupes(words, tree, args))


	# Process word list (automatic mode)
	meta_usage(True)
	process_list(words, tree, args)


	return True


def testall():
	"Test all the languages and rebuild their cache."
	all_cmds = []
	os.chdir(sys.path[0])		# change to local dir
	os.makedirs('test', exist_ok=True)
	print("All commands to be tested:")
	extra = []
	for item in sys.argv[1:]:
		if not '-testall' in item:
			extra.append(item)
	if extra:
		print('Extra command options:', extra)
		print('Press enter to continue.')
		input()



	def make_cmd(lang, out=None, freq=None):
		base = "wordtree.py --debug 3  --wikiroots".split()
		if not out:
			out = lang
		cmd = base + ['--csv', os.path.join('test', out + '.csv'), '--lang', lang]
		if freq:
			cmd += ['--freq', os.path.join('freq', freq + '.xz')]
		cmd += extra
		print(' '.join(cmd))
		all_cmds.append(cmd)

	# Standard languages
	for lang in sorted(LANGCODES.keys()):
		make_cmd(lang)

	# Serbo-Croation languages use code sh:
	# https://en.wikipedia.org/wiki/Serbo-Croatian
	for lang in 'bs sr hr'.split():
		make_cmd('sh', out=lang, freq=lang)

	# Run test
	for cmd in all_cmds:
		print('\n'*4)
		print("Testing with command:", cmd)
		sys.argv = cmd
		start = tpc()
		if not main():
			sys.exit(1)
		print('Total time:', rns((tpc() - start) / 60), 'minutes')


if __name__ == "__main__":
	if bool(os.name == 'nt') and sys.flags.utf8_mode == 0:
		eprint("\n\nWindows users must run this program with: python3 -X utf8")
		sys.exit(1)

	if not os.access('.', os.W_OK):
		print("Directory", os.getcwd(), "must be writable to store a cached version of the wikitionary database.")
		sys.exit(1)

	if '--testall' in sys.argv:
		testall()
	else:
		sys.exit(not main())
