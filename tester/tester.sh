#!/bin/bash

set -e

# Change to the directory where the script is located
cd "$(dirname "$0")"


title() {
	echo -e "\n\n\n\n$*"
	echo "================================================================"
}


title "Simple manual mode test. This will take awhile if you haven't built these cache folders yet."
echo -e "hello\nq\n" | ../wordtree.py --lang engli


title "Reading The Jungle Book"
../wordtree.py --anki --lang eng --rankbook The_Jungle_Book.txt --csv out.csv


title "Here is a sample from the csv file starting at line 2000:"
head out.csv -n 1
head out.csv -n 2000 | tail

title "Testing input list"
../wordtree.py --anki --lang eng --book The_Jungle_Book.txt input.txt --reverse --noentry > out.txt


title "Testing csv output"
../wordtree.py --lang eng --book The_Jungle_Book.txt --wikiroots --min 1 --max 10 --csv out.roots.csv


title "Showing words that were more common in book than in subtitles:"
sort -t, -k7,7nr out.roots.csv  | head

title "Testing a selection of word roots from the English language. This will take awhile."
../wordtree.py --wikiroots --lang eng --dupes input.txt --stars --nosort --min 1 --max 10 | gzip > out.wikiroots.txt.gz


title "Testing Arabic"
echo -e "مرحبًا\nq\n" | ../wordtree.py --lang ar arabic


title "Testing a selection of word roots from the Arabic language."
../wordtree.py --wikiroots --lang arab --min 1 --max 10 |  gzip > out.arabic.txt.gz


title "Testing RAE list. (Requires download)"
echo -e "pistear\nq\n" | ../wordtree.py --rae --lang spanish


title "Regenerating all language cache folders. This will take hours."
sleep 10 && ../wordtree.py --testall
