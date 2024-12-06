#!/bin/bash
set -e
mkdir -p test

# Run with:  reset; nice ./testall.sh
# Windows users can use cygwin to run this
# Some languages are commented out because they seem to be missing from the Wiktionary database.


lc=ar; lang=Arabic; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=bg; lang=Bulgarian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=bn; lang=Bengali; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=br; lang=Breton; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ca; lang=Catalan; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=cs; lang=Czech; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=da; lang=Danish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=de; lang=German; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=el; lang=Greek; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=eo; lang=Esperanto; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=es; lang=Spanish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=et; lang=Estonian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=eu; lang=Basque; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fa; lang=Persian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fi; lang=Finnish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fr; lang=French; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=gl; lang=Galician; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=he; lang=Hebrew; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hi; lang=Hindi; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hu; lang=Hungarian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hy; lang=Armenian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=id; lang=Indonesian; python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=it; lang=Italian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ja; lang=Japanese; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ka; lang=Georgian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=kk; lang=Kazakh; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ko; lang=Korean; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=lv; lang=Latvian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=mk; lang=Macedonian; python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ml; lang=Malayalam; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=nl; lang=Dutch; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=no; lang=Norwegian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=pl; lang=Polish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=pt; lang=Portuguese; python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ro; lang=Romanian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ru; lang=Russian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang

# Serbo-Croation languages use code sh:
# https://en.wikipedia.org/wiki/Serbo-Croatian
# lc=bs; lang=Serbo-Croatian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sh; lang=Serbo-Croatian;      python3 -X utf8 wordtree.py --wikiroots --sort --csv test/bs.csv --lang $lc $lang --freq freq/bs.xz	# Bosnian
lc=sh; lang=Serbo-Croatian; 	 python3 -X utf8 wordtree.py --wikiroots --sort --csv test/sr.csv --lang $lc $lang --freq freq/sr.xz	# Serbian
lc=sh; lang=Serbo-Croatian; 	 python3 -X utf8 wordtree.py --wikiroots --sort --csv test/hr.csv --lang $lc $lang --freq freq/hr.xz	# Croatian

lc=si; lang=Sinhalese; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sk; lang=Slovak; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sl; lang=Slovenian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sq; lang=Albanian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sv; lang=Swedish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ta; lang=Tamil; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=te; lang=Telugu; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=th; lang=Thai; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=tl; lang=Tagalog; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=tr; lang=Turkish; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=uk; lang=Ukrainian; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ur; lang=Urdu; 		python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=vi; lang=Vietnamese; python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=zh; lang=Chinese; 	python3 -X utf8 wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
