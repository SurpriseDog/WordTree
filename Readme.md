

## Install:
 1. Download the Wiktionary dump and put it in the same directory as wordtree.py
   - Link: https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2
   - Warning! This is a BIG file ≈ 2GB
 2. Choose your language and run with: wordtree.py --lang (language name)
   - For example to select Spanish you would run the program with: `wordtree.py --lang Spanish`
   - The first run will take many minutes to scan the entire 2 gigabyte Wiktionary dump file and process it into a sqlite3 database inside of the cache folder. After that, the program will start in a few seconds every time, unless you run it with a different language code.



**Windows Instructions**

Windows users will want to open a powershell and type: `python3 -X utf8 wordtree.py` (Make sure to capitalize the X) If you don't have Python3 yet, you can [download it from python.org](https://www.python.org/downloads/windows/) The `-X utf8` is required for Windows if your Python version is below [3.15](https://peps.python.org/pep-0686/)!

You won't be able to input non-ascii characters like **言葉** in powershell, until you change the font to "MS Gothic". [Instructions here.](https://learn.microsoft.com/en-us/troubleshoot/windows-server/system-management-components/powershell-console-characters-garbled-for-cjk-languages)


## Usage:

Detailed help can be found by running `wordtree.py --help`

In the meantime, here are some common ways to use it:


**Manual mode**

 * You can input individual words by just running `wordtree.py` in the terminal
 * It will attempt to autocorrect words missing diacritics. For example, it will convert organico to orgánico or tamano to tamaño.

![Example usage](example1.png)



**Inputing a list of words from a file**

Usage: `wordtree.py your_word_list.txt`

Word lists can be in csv format, text or the "My Clippings.txt" from Kindle E-reader. The easiest way to do this is just a simple text file with one word per line.
 * Words cannot contain spaces.
 * I have not tested any other Kindle's format besides my own. Let me know if it works or not for you and what version of Kindle you have.




**Comparing words with anki**

Usage: `--anki` will attempt to automatically guess the location of your .anki2 file assuming your user profile is 'User 1' - You can also type the location in manually with `--anki (database location)`


This will check to see if the words exist in your anki database, and prints matching cards. This is a read only copy of the database and will not change anything. (Sqlite3: mode=ro)

I find this useful to make sure I don't try to add the same card twice. If the database is busy (because you are using the anki app), it will switch to reading a cached version (if available). Closing anki should solve this problem and give you the most up-to-date copy of your cards.

Here are the locations of the anki databases.

 * Windows: %APPDATA%\Anki2
 * MacOS: ~/Library/Application Support/Anki2
 * Linux: ~/.local/share/Anki2

You can also select all of the notes in Anki and `Right-click->Notes->Export Notes`. Check the box to support older versions. Save as a .apkg file and open that instead with --anki (your location).apkg



**Compare words against a book**

Usage: `--book bookname.txt`

Optionally, you can compare the frequency of words against a book.

 * This must be a .txt file, not a .mobi, .pdf or any kind of e-reader format.
 * It will automatically strip punctuation from any words found. For example, if a word ends in a comma, "quotation mark" or period.



**Star words**

Usage: `--nostars`

Sometimes words have multiple meanings. For example "privado" means private, not just the past participle of "privar", so it’s fpm is way too high.

By eliminating the star words, I have it reporting privar at a total of 5 fpm vs 88 with all the star words.

![Example usage](example2.png)

In this example, privado has 3 stars meaning that it's fpm is much too high to be included in the total fpm for privar. The more stars, the more ridiculous the discrepancy.



**More features**

 Control how the output is sorted, set minimum and maximum fpms, output to csv and more.

 See additional help by running `wordtree.py --help`


**Known bugs**

Arabic columns are displayed backwards? It seems to work, but I need an Arabic speaker/learner to confirm that this output makes sense. Same goes for all other less common languages. I've tested the output in English and Spanish, but I'd appreciate it if other language speakers could tell me if the program works for their language of choice.


**Exceptions to the gender rules**

gender.py searches the Wiktionary database for nouns that don't follow the expected gender rules of a language. For example, La mano ends in an `o`, but is a feminine noun. You can specify any noun suffix for any language.

The program will try each suffix in turn so it will try `ión` = female, before trying `n` = male, because `ión` is listed in the second position of d-ión-z-a while `n` is in the third position of l-o-n-e-r-s.

Use `gender.py --help` for more information.


## Data sources:

 **Frequency List**

 The default subtitle frequency lists are from the OpenSubtitle project: https://opus.nlpl.eu/OpenSubtitles/corpus/version/OpenSubtitles

 Tokenization was done here: https://github.com/hermitdave/FrequencyWords

 It's authorized under the `CC-by-sa-4.0` license. I have compressed the 2018 files and removed words with less than 3 hits in the corpus to save space and improve loading times.

 The Wikipedia word frequency lists are from this github project: https://github.com/IlyaSemenov/wikipedia-word-frequency

 It's authorized under the `MIT license`. I have cut short every file that has more than a million lines to save space and improve loading times.
