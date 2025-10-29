#!/usr/bin/python3

import os
import sys
from time import perf_counter as tpc

from languages import CACHE
from tree import make_freq_table
from sd.common import rns, percent
from letters import strip_punct, eprint
from storage import make_or_load_json, open_any


def get_freq_table(filename):
	"Scan words in filename and convert to frequency table of word->freq"
	freq = dict()
	total = 0

	num = 0
	f = open_any(filename)
	
	start = tpc()
	default_freq = 200000
	update_freq = default_freq
		
	# info from last update
	# last_update = tpc()
	last_size = 0
	last_total = 0
	
	fix_symbols = str.maketrans({"’":"'", "‘":"'", "‛":"'", "′":"'", "ʼ":"'", "＇":"'", "´":"'", "–":"-", "—":"-", "−":"-", "-":"-"})


	for line in f:
		num += 1
		for word in line.split():
			total += 1
			word = strip_punct(word).translate(fix_symbols)

			# Ignore all capitalized words. Will ignore words at beginning of sentences as well.
			# if word.istitle():
			#	continue
			word = word.lower()
			
			if word in freq:
				freq[word] = freq[word] + 1
			else:
				freq[word] = 1
				new_word = word
		if not num % update_freq:
			if num == update_freq:
				eprint("Note: wpm = unique words found per million words read\n")
		
			size = len(freq)
			update = tpc()
			wps = num / (update - start)
			eprint("Reading line:", rns(num), 'at', rns(wps), 'lines per second.', \
			'Dictionary size:', rns(size), \
			# unique words per second:
			# "growing at", rns((size - last_size) / (update - last_update)), 'wps', \
			# unique words per million words read
			"growing at", rns((size - last_size) / (total - last_total) * 1e6), 'wpm', \
			"Unique word:", new_word)
			last_total = total
			# last_update = update
			last_size = size
			if num == default_freq * 5:
				update_freq = default_freq * 5
			
	f.close()
	
	ufreq = len(freq) / total
	ufreq = percent(ufreq, 2)	
	eprint("Processed:", rns(total), 'words and found', rns(len(freq)), 'unique words =', ufreq, '\n')

	freq['__TOTAL__'] = total
	return freq
	
	

def detect_book(filename, threshold=16, verbose=True):
	"Count up how many words per line in text and determine if it should be read like a book or a list"
	wpl = []		# words per line
	#with open(filename) as f:
	f = open_any(filename)
	for line in f:
		line = line.split()
		wc = 0				# word count per line
		for word in line:
			# eprint(wc, word)
			if word.startswith('#'):
				break
			wc += 1

		if wc:
			wpl.append(wc)
			# eprint(len(wpl), wc, line)
			if len(wpl) >= 2100:
				# sample error rate approaching 2%
				break
	f.close()


	# chop off the first few dozen lines of book to avoid counting up non-prose intro
	# eprint(wpl)
	if len(wpl) >= 400:
		wpl = wpl[100:]
	wpl = sum(wpl) / len(wpl) if wpl else 0
	if verbose:
		eprint("Detected an average of", int(round(wpl, 0)), "words per line from input file.")
	if wpl >= threshold:
		return True
	return False
	
	
def load_book(filename):
	"Convert book into frequency table or load cached file."
	
	if not os.path.exists(filename):
		eprint("Can't find path:", filename)
		sys.exit(1)
	
	try:
		is_freq = not detect_book(filename, threshold=3, verbose=False)
	except UnicodeDecodeError:
		# happens with compressed files
		is_freq = False
	
	
	if is_freq:
		eprint("\nIt appears that", filename, "is not actually a book so I'm trying to load it as a frequency table...\n")
		# Load a frequency table if that was supplied instead of a book
		freq, total = make_freq_table(filename)	
		freq['__TOTAL__'] = total
		return freq
	
	eprint("Loading:", filename)
	book = make_or_load_json(os.path.join(CACHE, os.path.basename(filename) + '.json'), get_freq_table, filename)	
	return book	
