

## Install:
 1. Download the Wiktionary dump and put it in the same directory as ./wordtree.py
   - Link: https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2
   - Warning! This is a BIG file ≈ 2GB
 2. Choose your language and run with: ./wordtree.py --lang (abbreviation) (Language Name)
   - For example to choose French you would run the program with: `./wordtree.py --lang fr French`
   - The first run will take many minutes to scan the entire wiktionary dump and process it into a database inside the cache folder. After that, the program will start in a few seconds everytime.

Note: I have only tested this in Linux. If it breaks in Windows or Mac, give me the error output and I'll try to fix it.


## Usage:

Detailed help can be found by running ./wordtree.py --help

In the meantime, here are some common ways to use it:


**Manual Mode**

 * You can input individual words by just running ./wordtree.py in the terminal
 * It will attempt to autocorrect words missing diacritics like convert organico to orgánico or tamano to tamaño.


**Inputing a list of words**

 Word lists can be in csv format, text or the "My Clippings.txt" from kindle E-reader
 * One word per line
 * Words cannot have any spaces in them.
 * It will automatically strip punctuation from any words found. Such as if a word ends in a comma, "quotation mark" or period.
 * I have not tested any other Kindle's format besides my own. Let me know if it works or not for you and what version kindle you have.

 Usage: ./wordtree.py (your word_list.txt)


**Comparing words against anki**

Checks against your anki database, and prints matching cards. I find this useful to make sure I don't try to add the same card twice. The anki database is read in read only mode. If the database is busy (because you are using the anki app), it will switch to reading a cached version (if available).

Here are the locations of the anki databases.

 * Windows: %APPDATA%\Anki2
 * MacOS: ~/Library/ApplicationSupport/Anki2
 * Linux: ~/.local/share/Anki2

**Compare words against a book**

 Optionally you can compare the frequency of words against a book. This must be a .txt file, not a .mobi, .pdf or any kind of e-reader format.


**More**

 Control how the output is sorted, output to csv and more. See additional help by running ./wordtree.py --help



## Data sources:

 **Frequency List**

 The frequency lists are from the OpenSubtitle Project: http://opus.nlpl.eu/OpenSubtitles2018.php

 Tokenization was done here: https://github.com/hermitdave/FrequencyWords

 It's authorized under the CC-by-sa-4.0 license. I have compressed the 2018 files and removed words with less than 3 hits in the corpus to save space and improve loading times.
