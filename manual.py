#!/usr/bin/python3


import os
import sys
import signal

from word import Word
from letters import eprint, COMMON_SYMBOLS

IS_WINDOWS = bool(os.name == 'nt')


def user_word(text):
	"Get user input while ignoring ctrl-C or Z"
	def interrupt(*_):
		print("\nType q to quit")
		
	def get_word():	
		word = ''
		try:
			word = input(text)
		except EOFError:
			interrupt()	
		return word	

	if IS_WINDOWS:
		word = get_word()
	else:				
		signal.signal(signal.SIGINT, interrupt)		# Catch Ctrl-C
		signal.signal(signal.SIGTSTP, interrupt)	# Catch Ctrl-Z
		word = get_word()
		signal.signal(signal.SIGINT, lambda *args: sys.exit(1))
		signal.signal(signal.SIGTSTP, lambda *args: sys.exit(1))
	return word.strip()
	
	
def arrows(word):
	# Count arrows. Only works in linux
	up = word.count('\x1b[A') + word.count('\x1bOA')
	down = word.count('\x1b[B') + word.count('\x1bOB')
	# print('debug arrows', up - down, repr(word))
	return up - down	



class ManualInput:
	history = []

	def __init__(self, tree, args, words=None):
		self.tree = tree
		self.args = args
		if not words:
			words = []
		self.words = words
		self.count = 0

	def show_word(self, word, **kargs):
		"Lookup word and check against dupe count (if available)"
		dupes = 1
		word = Word(word, self.tree, self.args)
		root = word.root
		if root in self.words:
			word.dupes = self.words[root].dupes + 1
		return word, word.print_info(self.tree, self.args, **kargs)

	def show_history(self, lines=1):
		return self.print_history()
		
		'''
		if not self.history:
			return
		if lines == -1:
			text = ' '.join(self.history)
		else:
			for x in range(20 * lines, 0, -1):
				text = ' '.join(self.history[-x:])
				if len(text) <= 80 * lines:
					break
		print("History:", text)
		'''

	def print_history(self):
		if self.history:
			print("\nHistory:")
			for word in self.history:
				if ' ' in word:
					print('#', word)
					continue
				_, out = self.show_word(word, quiet=True)
				for line in out[1:]:
					print(' '.join(line))

	def add_word(self, word):
		if word not in self.history[-2:]:
			self.history.append(word)

	def repeating(self, letters):
		return True if len(set(letters)) == 1 else False
		
	
	def process_cmd(self, word):
		split = word.split()
		cmd = split[0] if word else ''
		if self.repeating(word) or cmd in 'fd':
			if cmd == 'q':
				self.print_history()
				sys.exit(0)

			elif cmd.startswith('d'):
				if self.repeating(word):
					for d in range(len(cmd)):
						if self.history:
							word = self.history.pop(-1)
							print("Removed:", word)
					if len(cmd) > 1:
						self.print_history()
				else:
					word = word[2:].strip()
					if word in self.history:
						print('deleting:', word)
						self.history.remove(word)
					else:
						print("Can't find in history:", word)

			elif cmd == 'f':
				try:
					freq_table = split[1].strip("'").strip('"')
				except IndexError:
					freq_table = self.args.freq
				print("Loading:", freq_table)
				self.tree.load_table(freq_table, extended=True)

			elif cmd.startswith('h'):
				self.show_history(len(word))

			elif cmd == 'p':
				self.print_history()

			elif cmd == 's':
				pass
				
			elif cmd == 'c':
				self.args.wikiclean = int(not self.args.wikiclean)
				print('--wikiclean set to', self.args.wikiclean)

			elif cmd == 'a' and self.history:
				old = self.args.showall
				self.args.showall = True
				self.show_word(self.history[-1])
				self.args.showall = old

			elif cmd == 'w' and self.history:
				word = self.history[-1]
				word_obj = Word(self.tree.check_spelling(word), self.tree, self.args)
				word_obj.print_entry(self.tree, root=False, wikiclean=self.args.wikiclean)
				return word

			else:
				print("Command not recognized. Type help for command list.")
			return ''
		else:
			return word
			
				

	def run(self):
		word = ''
		while True:
			self.count += 1
			print("")
			if not word:
				print('\n' * 3)
				if self.count == 1:
					print("Common accented characters ready to copy-paste:\n")
				print(COMMON_SYMBOLS, '\n')
				word = user_word('Input word or type help for more commands: ').strip()

			if arrows(word):
				if arrows(word) < 0:
					self.show_history(lines=abs(arrows(word)))
					word = ''
					continue
				else:
					try:
						word = self.history[-(arrows(word))]
						print("Replaying word:", word)
					except IndexError:
						self.show_history()
						word = ''
						continue

			if not word:
				continue

			if word == 'help':
				if os.path.exists('help.txt'):
					for line in open('help.txt').readlines():
						if not line.startswith('#'):
							eprint(line.rstrip().replace('\t', ' ' * 4))
				else:
					eprint("Error: help.txt is missing")
				word = ''
				continue

			word = self.process_cmd(word)
			if not word or word == 'w':
				word = ''
				continue		

			if ' ' in word:
				print("Multiple word phrases are not supported.")
				self.add_word(word)
				word = ''
			else:
				word = self.tree.check_spelling(word.lower())
				self.add_word(word)

			word, _ = self.show_word(word)

			if not self.args.noentry and self.tree.get_entry(word.root):
				i = user_word("\nPress enter to show root entry, type w to show word entry, or type new word: ")
				if i.lower() == 'w':
					word.print_entry(self.tree, root=False, wikiclean=self.args.wikiclean)
					word = ''
				elif not i:
					word.print_entry(self.tree, wikiclean=self.args.wikiclean)
					word = ''
				else:
					word = i
			else:
				word = ''
				


def manual_input(tree, args, words=[]):
	mi = ManualInput(tree, args, words)
	mi.run()
