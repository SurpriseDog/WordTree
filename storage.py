#!/usr/bin/python3

import os
import csv
import sys
import itertools
from time import perf_counter as tpc

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from letters import eprint
from sd.common import rns, rfs


'''
def timeit(func, *args, timeit_txt='Ran function in', **kargs):
    start = tpc()
    out = func(*args, **kargs)
    print(timeit_txt, rns(tpc() - start), 'seconds')
    return out
'''


def loading(name, header="Loading", newline=False):
    if newline:
        end = '\n'
    else:
        end = ' '
    eprint(header, name + '...', end=end, flush=True)
    return tpc()


def print_elapsed(start, newline=False, mint=0.1):
    end = tpc()

    # Don't print time for super quick runs
    if end - start < mint:
        if not newline:
            eprint('')
        return

    if newline:
        header = '\tDone in'
    else:
        header = ''

    eprint(header, rns(end - start) + ' seconds', flush=True)

def make_or_load_json(filename, function, *args):
    "Load json data set or run function to make it."
    if not os.path.exists(filename):
        # print("Making", filename + '...')
        data = function(*args)
        with open(filename, 'w') as out:
            json.dump(data, out)
    else:
        if os.path.getsize(filename) >= 1e6:
            start = loading(filename)
            data = json.load(open(filename))
            print_elapsed(start)
        else:
            data = json.load(open(filename))
    return data


def dump_roots(filename, dct):
    "Convert dict to csv"
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        writer.writerows([i[0]] + [y for x in i[1] for y in x] for i in dct.items())


def load_roots(filename):
    "Convert csv to dict"
    out = dict()
    with open(filename, 'r') as csv_file:
        for row in csv.reader(csv_file):
            # print(row)
            out[row[0]] = list(zip(*[iter(row[1:])]*2))
            # print(row[0], ':', out[row[0]], '\n'*2)
    return out


def dump_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_json(filename, ok_missing=False):
    if not os.path.exists(filename):
        if ok_missing:
            return dict()
        else:
            raise ValueError("Missing file!", filename)
    with open(filename) as f:
        return json.load(f)


def dump_csv(filename, dct, chain=False, printme=False):
    '''
    Convert dict to csv
    chain will mash together nested lists
    '''
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        for key, val in dct.items():
            if chain:
                row = [key] + list(itertools.chain.from_iterable(val))
            else:
                row = [key] + val
            writer.writerow(row)

            if printme:
                print('\n\nkey:', key)
                print('\nval:', val)
                print('\nrow:', row)



def load_csv(filename, chunk=0):
    '''
    Convert csv to dict
    chunk will group together every n items into a sublist
    '''
    out = dict()
    with open(filename, 'r') as csv_file:
        if chunk:
            for row in csv.reader(csv_file):
                out[row[0]] = list(zip(*[iter(row[1:])]*chunk))
        else:
            for row in csv.reader(csv_file):
                out[row[0]] = row[1:]

    return out


def comp_dict(dic1, dic2, convert_tuples=False, printme=0):
    "Compare two dictionaries"
    # comp
    count = 0
    for key in dic1:
        count += 1
        val1 = dic1[key]
        val2 = dic2[key]
        if convert_tuples:
            # Convert tuples to lists
            val1 = list(map(list, val2))
            val2 = list(map(list, val2))

        if val1 != val2:
            print('\n\n\nKey:', key)
            print('\nd1:', val1)
            print('\nd2:', val2)
            print('File conversion failed.')
            return False
        elif count <= printme:
            print('\nKey:', key)
            print('match:', str(val1)[:300])
            print('match:', str(val2)[:300])
        # print(d2[key])
    return True


def convert_json2csv(filename, chunk=0):
    "Convert a json to csv and check each row"

    ofile = os.path.splitext(filename)[0] + '.csv'
    print("Convert json to csv:", filename, ofile)

    if not os.path.exists(filename):
        raise ValueError("Can't find filename:", filename)
    d1 = load_json(filename)

    dump_csv(ofile, d1, chain=bool(chunk))
    d2 = load_csv(ofile, chunk=chunk)

    if not comp_dict(d1, d2, convert_tuples=bool(chunk)):
        sys.exit(1)



def convert_and_load(filename, chunk=0, use_json=False, testing=False, force_convert=False):
    "Convert json to csv or load csv directly if available."

    if not testing:
        if use_json:
            # Return json directly for some files
            return load_json(filename)

    if testing:
        print("\n\nTesting .json load for", filename, rfs(os.path.getsize(filename)))
        start = tpc()
        data1 = load_json(filename)
        json_t = tpc() - start
        print_elapsed(start, mint=0)

    csv_name = os.path.join(os.path.splitext(filename)[0] + '.csv')
    if not os.path.exists(csv_name) or force_convert:
        convert_json2csv(filename, chunk=chunk)

    if testing:
        print("Testing .csv load for", csv_name, rfs(os.path.getsize(csv_name)))
        start = tpc()
        data2 = load_csv(csv_name, chunk=chunk)
        csv_t = tpc() - start
        print_elapsed(start, mint=0)
        if csv_t < json_t:
            print('Saved:', int(100 - csv_t / json_t * 100), 'percent')
        else:
            print('CSV was slower!')

        if comp_dict(data1, data2, convert_tuples=bool(chunk)):
            print("Dictionaries match!")
        return data2
    else:
        return load_csv(csv_name, chunk=chunk)


def tester(lang):
    directory = os.path.join('cache', lang)
    os.chdir(directory)
    print("Using directory:", os.getcwd())

    if 'ujson' in sys.modules:
        print("Using ujson module")


    '''
    Only used once, so I'm using .json
    print('Testing roots.csv')
    r1 = load_roots('roots.csv')
    dump_csv('roots_test.csv', r1, chain=True)
    r2 = load_csv('roots_test.csv', chunk=2)
    comp_dict(r1, r2)
    print('roots.csv matches')
    '''


    testing = True
    convert_and_load('tree.json', chunk=3, testing=testing)
    convert_and_load('reverse.json', testing=testing)
    # convert_and_load('spelling.json', testing=testing)



if __name__ == "__main__":
    # import json
    tester(sys.argv[1] if len(sys.argv) > 1 else 'es')
