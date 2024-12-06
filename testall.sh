#!/bin/bash
set -e
mkdir -p test

# Run with:  reset; nice ./testall.sh
# Some languages are commented out because they seem to be missing from the Wiktionary database.


lc=ar; lang=Arabic; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=bg; lang=Bulgarian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=bn; lang=Bengali; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=br; lang=Breton; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ca; lang=Catalan; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=cs; lang=Czech; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=da; lang=Danish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=de; lang=German; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=el; lang=Greek; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=eo; lang=Esperanto; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=es; lang=Spanish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=et; lang=Estonian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=eu; lang=Basque; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fa; lang=Persian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fi; lang=Finnish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=fr; lang=French; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=gl; lang=Galician; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=he; lang=Hebrew; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hi; lang=Hindi; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hu; lang=Hungarian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=hy; lang=Armenian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=id; lang=Indonesian; ./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=it; lang=Italian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ja; lang=Japanese; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ka; lang=Georgian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=kk; lang=Kazakh; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ko; lang=Korean; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=lv; lang=Latvian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=mk; lang=Macedonian; ./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ml; lang=Malayalam; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=nl; lang=Dutch; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=no; lang=Norwegian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=pl; lang=Polish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=pt; lang=Portuguese; ./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ro; lang=Romanian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ru; lang=Russian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang

# Serbo-Croation languages use code sh:
# https://en.wikipedia.org/wiki/Serbo-Croatian
# lc=bs; lang=Serbo-Croatian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sh; lang=Serbo-Croatian;      ./wordtree.py --wikiroots --sort --csv test/bs.csv --lang $lc $lang --freq freq/bs.xz	# Bosnian
lc=sh; lang=Serbo-Croatian; 	 ./wordtree.py --wikiroots --sort --csv test/sr.csv --lang $lc $lang --freq freq/sr.xz	# Serbian
lc=sh; lang=Serbo-Croatian; 	 ./wordtree.py --wikiroots --sort --csv test/hr.csv --lang $lc $lang --freq freq/hr.xz	# Croatian

lc=si; lang=Sinhalese; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sk; lang=Slovak; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sl; lang=Slovenian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sq; lang=Albanian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=sv; lang=Swedish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ta; lang=Tamil; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=te; lang=Telugu; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=th; lang=Thai; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=tl; lang=Tagalog; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=tr; lang=Turkish; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=uk; lang=Ukrainian; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=ur; lang=Urdu; 		./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=vi; lang=Vietnamese; ./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
lc=zh; lang=Chinese; 	./wordtree.py --wikiroots --sort --csv test/$lc.csv --lang $lc $lang
