#!/usr/bin/python3
# List all anki notes in database
# Testing: run as ./myanki.py <.anki2 or .apkg filename>

import os
import sys
import time
import shutil
import sqlite3
import zipfile
import hashlib

def eprint(*args, **kargs):
	args = list(args)
	if args:
		args[0] = '\t' + str(args[0])
	print(*args, file=sys.stderr, **kargs)


def sanitize(s, bits=128):
	"Turn a string into a valid filename."
	return hashlib.sha512(s.encode()).hexdigest()[:(bits//4)]


def read_database(filename, retries=3):
	"Read notes with read only connection"

	for tri in range(retries + 1):
		if tri:
			eprint("Retrying", tri, 'of', str(retries) + '...')
			time.sleep(1 + tri * 2**0.5)
		eprint("Connecting to database:", filename)
		con = sqlite3.connect('file:' + filename + '?mode=ro', timeout=1, uri=True)
		cur = con.cursor()
		try:
			tables = cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
			tables = [x[0] for x in tables]
		except sqlite3.OperationalError as err:
			con.close()
			eprint("Error:", err)
			continue

		# Database structure: https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
		notes = cur.execute("SELECT id, mod, flds, tags, mid FROM notes").fetchall()

		# Associate notes with decks
		cards = cur.execute("SELECT nid, id, did, queue, ord FROM cards").fetchall()

		# Associate deck names with ids

		if 'decks' in tables:
			decks = cur.execute("SELECT id, name FROM decks").fetchall()
		else:
			eprint("No deck table in database.")
			decks = []

		break

	else:
		eprint("\nFailed to connect to database.")
		eprint("Make sure the filename is correct or try closing anki before proceeding.")
		return None, None, None

	con.close()
	return notes, cards, decks




def getnotes(filename):
	'''Fetch all data from anki filename and return dictionary'''
	if not os.path.exists(filename):
		eprint("Can't find filename:", filename)
		sys.exit(1)

	ext = os.path.splitext(filename.lower())[-1]

	if ext == '.apkg':
		try:
			tmp = zipfile.ZipFile(filename).extract('collection.anki21', 'cache')
		except KeyError:
			eprint("Try using the option to 'Support older versions of Anki' when exporting")
			sys.exit(1)
		notes, cards, decks = read_database(tmp)
		os.remove(tmp)
	else:
		# Read cards and/or make/read a cached copy of database
		cached = sanitize(os.path.abspath(filename)) + ext
		cached = os.path.join('cache', cached)
		notes, cards, decks = read_database(filename, retries=0)

		if notes:
			# Make a cached copy if anki database is readable and more than x seconds newer than cached
			if not os.path.exists(cached) or os.path.getmtime(filename) - os.path.getmtime(cached) >= 60:
				eprint("Make cache of database in:", cached)
				shutil.copy(filename, cached)
		else:
			if os.path.exists(cached):
				eprint("Using cached anki database:", cached)
				notes, cards, decks = read_database(cached, retries=0)
			else:
				sys.exit(1)




	# Change cards into dictionary of note id -> deck id
	# nid = note id
	# id = card id
	# did = deck id
	# queue = queue (suspended, new...)
	cards_src = cards
	cards = dict()
	for nid, id, did, queue, ord in cards_src:
		if nid not in cards:
			cards[nid] = dict()
		cards[nid][id] = [did, queue, ord]

	# Get deck names
	decks = {id:name.split('\x1f') for id, name in decks}

	# Combine everything into a dictionary
	col = dict()
	for nid, mod, flds, tags, mid in notes:
		# process fld to split into question, answer and minor txt processing
		out = dict()
		line = flds.split('\x1f')
		out['question'] = line[0].replace('&nbsp;', ' ').replace('<br>', '\n')
		out['ans'] = line[1]
		out['fields'] = line
		out['mid'] = mid

		# eprint(line[0])

		# Look at cards
		out['decks'] = set()
		out['queues'] = list()
		out['cards'] = dict()
		# todo change this into a list ordered by ord
		for card, (did, que, order) in cards[nid].items():
			ci = dict()
			ci['order'] = order
			ci['deck_id'] = did
			ci['deck'] = '::'.join(decks.get(did, ['unknown_deck',]))
			out['decks'].add(ci['deck'])
			ci['queue'] = que
			out['queues'].append(que)
			out['cards'][card] = ci
			if order == 0:
				out['deck'] = '::'.join(decks.get(did, ['unknown_deck',]))
				out['queue'] = que

		'''
		out['deck_id'] = list(set([did for did, que in ci.values()]))		# List of decks
		out['cards'] = {card:que for card, (did, que) in ci.items()}		# card to que
		out['decks'] = [decks[did] for did in out['deck_id']]
		out['queue'] = list(out['cards'].values())
		'''

		out['mod'] = mod
		out['tags'] = tags.strip().split()
		col[nid] = out			# nid is id of the note
		# eprint(out,'\n\n')

	return col


def _tester():
	notes = getnotes(sys.argv[1]).items()
	for question, ans in notes:
		eprint(question, ans, '\n', sep='\t')
	eprint("Found", len(notes), 'notes')


if __name__ == "__main__":
	_tester()
