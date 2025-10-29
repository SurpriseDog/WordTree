#!/usr/bin/python3


import sys
import math
import traceback

from tree import show_fpm
from wikitext import clean_wikitext
from sd.columns import auto_columns

# Testing: ./word.py (dupefactor)

def log_weighted_avg(a, b, factor=1, verbose=False):
	'''
	Frequencies a and b are better averaged with logs
	factor is the weighting factor applied to number a
	negative factors apply the weighting factor to b
	'''
#
	# 0 probably means missing from the table
	# Every word should have SOME frequency for averaging,
	# otherwise 0 is infinitely small compared to the other number
	# and will drag that number into toward it's infinite smallness.
	# therefore we switch to a simple weighted average
	if factor < 0:
		factor = abs(factor)
		a, b = b, a
		
#	
	if a <= 0 or b <= 0:
		result = (a * factor + b) / (factor + 1)
	else:
		result = 1e6 * 10**((math.log10(a/1e6) * factor + math.log10(b/1e6)) / (factor + 1))
			# divide by factor + 1 because value b gets a weight of 1
			# technically the 1e6 cancels out, but it makes more sense this way
			# the log base doesn't matter. natural log would work the same here, but this is more intuitive.
	if verbose:
		print(a, b, result)
	return result

	

class Word:
	"Calculate a word's root and fpm"

	def __init__(self, word, tree, args, branch=None):
		self.extra = []
		if type(word) == list:
			self.extra = word[1:]
			word = word[0]
		self.word = word
		self.fpm = tree.get_fpm(word)
		self.branch = branch
		
		self.dupes = 1		# Duplicates found of this word
		self.root = tree.find_root(word, silent=True) or word
		self.derived, book_count = self.get_freq(tree, args)

		# Book fpm
		self.book_fpm = 0
		self.book_count = book_count
		if args.book:
			self.book_fpm = book_count / args.book['__TOTAL__'] * 1e6 if args.book else 0


	def get_freq(self, tree, args, silent=True):
		# total_freq
		# threshold = args.threshold if threshold == -1 else threshold
		# return tree.total_freq(self.word, book=args.book, nostars=(not args.stars), highstars=args.starval, silent=silent, threshold=threshold, branch=self.branch)
		return tree.total_freq(self.word, args, silent=silent, branch=self.branch)
		


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


	def calc_adj(self, args):
		"Calculate the fpm after adjustment"
		# Calculate the adjustment based on book frequency and dupes.			
		fpm = self.derived
		
		if self.book_fpm:
			bf = args.bookfactor / 100		# Convert bookfactor to a float		
		
			# fpm = (self.book_fpm * bf + self.derived) / (bf + 1)	# Weighted average
			fpm = log_weighted_avg(self.book_fpm, self.derived, bf)		
					
		if self.dupes > 1:
			if fpm <= 0.01:
				fpm = 0.01			# little boost to help words with 0 fpm and many dupes
			# fpm *= dupe_calc(self.dupes, args.dupefactor / 10)		# s shaped curve
			# fpm *= dupe_calc(self.dupes, args.dupefactor)
			if fpm < 0.001:
				fpm = 0.01		# small boost to help words with 0 fpm and many dupes
			fpm = log_weighted_avg(fpm * self.dupes, fpm, args.dupefactor/100, verbose=False)
				# why this works, nobody knows
			
			
		return fpm


	def skipped(self, args):
		# check if word should
		if args.max and self.derived > args.max:
			return True
		if args.min and self.derived < args.min:
			return True
		if args.skipanki and self.check_anki(args.anki):
			return True
		return False


	def print_entry(self, tree, root=True, wikiclean=1):
		def print_wikiclean(entry):
			try:
				print(clean_wikitext(entry))
			except Exception as e:		# pylint: disable=W0718
				traceback.print_exc(e)
				print("\nclean_wikitext failed! Please report this issue on Github\n")
				print("Original entry:")
				print(entry)	
			
		
	
		if root:
			word = self.root or self.word
		else:
			word = self.word
		entry = tree.get_entry(word)
		if entry:
			print("\nWiktionary entry for:", word, '\n')
			# print('debug wikiclean', wikiclean)
			
			if wikiclean == 0:
				print(entry)
			elif wikiclean == 1:
				print_wikiclean(entry)
			else:
				# level 2 (debug) - print both
				print(entry)
				print('\n\n')
				print('#'*18)
				print_wikiclean(entry)



	def print_info(self, tree, args, quiet=False):
		'''
		Print the info of a word given
		compact will only print the fpm line
		'''

		if not quiet:
			print("#" * 80)
			print("Processing word:", self.word, 'at', show_fpm(self.fpm) + ':',
				  "           (Card already in Anki)" if self.check_anki(args.anki) else '')

			# Show matches in anki database
			if args.anki:
				self.print_anki(args.anki)

			# Print total_freq tree and get bc (the book count)
			print('')
			print('')
			self.get_freq(tree, args, silent=False)


		# Get book frequency of word
		out = [' '.join((self.word, show_fpm(self.fpm))).strip(), '']
		
		if self.root and self.root != self.word:
			out[1] = ' '.join((' ', self.root, show_fpm(tree.get_fpm(self.root)))).strip()

		# Total
		out.append('Total: ' + show_fpm(self.derived))
		if self.book_fpm:
			out.append('Book: ' + show_fpm(self.book_fpm))


		adj = self.calc_adj(args)
		if adj != self.derived:
			out.append('Adj: ' + show_fpm(adj))

			
		# Add dupes if greater than 1 (the loneliest number)
		if self.dupes > 1:
			out.append('Dupes: ' + str(self.dupes))

		spaces = [20, 20, 16, 15, 14]
		
		# Create more space for the first column if the second column is empty
		if not out[1].strip() and len(out[0]) > 20:
			spaces[1] -= max(len(out[0]) - 20, 20)
			
		spaces = [' ' * n for n in spaces]

		out2 = auto_columns([spaces, out], space=2, printme=(not quiet), wrap=999)
		# print('debug out2', out)
		if quiet:
			return out2
		else:
			print('_' * len(out))
			

		return True
		
		
if __name__ == "__main__":

	for x in range(1, 20):
		print(x, log_weighted_avg(1, x, int(sys.argv[1])))
		
	print("\n\nThis is word.py - You probably intended to run ./wordtree.py")
