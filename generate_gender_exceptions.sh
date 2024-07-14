#!/bin/bash
# Generate all lists of exceptions to the gender rules
ex="Exceptions to the gender rules"


# Spanish
./gender.py --ending ma > "$ex/spanish_ma_nouns.txt"
./gender.py --ending o > "$ex/spanish_o_nouns.txt"
./gender.py > "$ex/spanish_all_nouns.txt"


# French
# https://french.stackexchange.com/questions/2616/is-there-any-general-rule-to-determine-the-gender-of-a-noun-based-on-its-spellin
./gender.py --lang fr -sf a e é ion -sm me o t > "$ex/french_all_nouns.txt"
