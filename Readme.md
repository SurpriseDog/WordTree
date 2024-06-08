

Install:
	1. Download the Wiktionary dump and put it in the same directory as ./wordtree.py
	     Link: https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2
	     Warning! This is a BIG file.
	2. (optional) - Choose a new language.
		* For example to choose French you would run the program with: --lang fr French



Usage:

	**Manual Mode**
	* You can input individual words by just running ./wordtree.py in the terminal



	**Input a list of words**
	Word lists can be in csv format, text or the My Clippings.txt from kindle E-reader
	* One word per line
	* words cannot have any spaces in them

	Usage: ./wordtree.py (your word list.txt)


	**Compare words against anki**
	todo point to anki file (tell where is)
	The anki database is read in read only mode. If the database is busy it will switch to reading a cached version.


	**Compare words against a book**
	todo point to a book




	**More**
	Control how the output is sorted, output to csv and more. See additional help by running ./wordtree.py --help






Features:
	Autocorrect words missing diacritics like convert organico to orgánico or tamano to tamaño.

	Read txt, csv or Kindle's My clippings.txt format
		This works on my old kindle, but I need more samples to see if it works on other generations.
		Automatically strip punctuation from words found

	Read from the anki database. (Don't worry, I'm using read only mode; no changes will be made). If you get a database is locked error, then just wait for anki to finish up or shutdown anki first. You can also read from an exported .apkg file. Wordtree makes a cache of the database after a sucessful read, and will pull words from that cache if the database is locked.



Data sources:
	**Frequency List**
	The frequency lists are from the OpenSubtitle Project: http://opus.nlpl.eu/OpenSubtitles2018.php
	Tokenization was done here: https://github.com/hermitdave/FrequencyWords
	It's authorized under the CC-by-sa-4.0 license
	I have compressed the 2018 files and removed words with less than 3 hits in the corpus to save space and improve loading times.
