#!/bin/bash
set -e
mkdir -p test

# Run with:  reset; nice ./testall.sh
# Windows users can use cygwin to run this


lc=ar;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=bg;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=bn;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=br;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ca;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=cs;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=da;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=de;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=el;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=en;		python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=eo;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=es;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=et;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=eu;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=fa;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=fi;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=fr;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=gl;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=he;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=hi;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=hu;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=hy;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=id;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=it;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ja;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ka;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=kk;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ko;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=lv;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=mk;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ml;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=nl;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=no;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=pl;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=pt;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ro;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ru;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc

# Serbo-Croation languages use code sh:
# https://en.wikipedia.org/wiki/Serbo-Croatian
# lc=bs;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=sh;       python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/bs.csv --lang $lc --freq freq/bs.xz	# Bosnian
lc=sh;  	 python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/sr.csv --lang $lc --freq freq/sr.xz	# Serbian
lc=sh;  	 python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/hr.csv --lang $lc --freq freq/hr.xz	# Croatian

lc=si;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=sk;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=sl;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=sq;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=sv;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ta;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=te;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=th;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=tl;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=tr;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=uk;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=ur;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=vi;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
lc=zh;  	python3 -X utf8 wordtree.py --debug 1  --wikiroots --sort --csv test/$lc.csv --lang $lc
