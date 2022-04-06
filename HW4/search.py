#!/usr/bin/python3
import math
import pickle
import re
import nltk
import sys
import getopt
from heapq import heappop, heappush, heapify

PORTER_STEMMER = nltk.stem.porter.PorterStemmer()


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding
    token = PORTER_STEMMER.stem(token)  # porter-stemming
    return token


def retrieve_postings_list(dictionary, term_id):
    """
    Takes a term id and retrieves its posting list by using the dictionary to find the offset
    in the file the posting list was written to. Returns said postings list.
    """
    with open(postings_file, 'rb') as read_postings:
        reader_offset = dictionary[term_id][1]
        read_postings.seek(reader_offset)
        return pickle.load(read_postings)


def search_term(term_to_search, dictionary, term_to_term_id):
    """
    Converts a term (str) to a posting list. Tries to first convert the term (str) to a term id (int) and
    then uses this term id to call a function that retrieves the posting list.
    """
    if term_to_search not in term_to_term_id:
        return []  # if the query term does not exist in dictionary, return an empty posting list

    term_id = term_to_term_id[term_to_search]
    return retrieve_postings_list(dictionary, term_id)


def merge_postings(a, b):
    """
    Find the intersection between two lists.
    Time Complexity: O(x + y)
    """
    print("BEGIN MERGE ...")
    resulting_postings = []

    # Base case. An AND operation always return null (empty list) if one of the lists are empty
    if not a or not b:
        return []

    a_length = len(a)
    b_length = len(b)

    a_idx = 0
    b_idx = 0

    while a_idx < a_length and b_idx < b_length:
        if a[a_idx][0] == b[b_idx][0]:
            resulting_postings.append(a[a_idx])
            a_idx += 1

        elif a[a_idx][0] < b[b_idx][0]:
            if a_idx + 1 == a_length:
                # can not be any more matches if this is satisfied.
                # this line is added to avoid IndexError in the following line
                return resulting_postings

            if a[a_idx + 1][2] != 0 and b[b_idx][0] - a[a[a_idx + 1][2]][0] >= 0:
                a_idx = a[a_idx + 1][2]
            else:
                a_idx += 1

        elif a[a_idx][0] > b[b_idx][0]:
            if b_idx + 1 == b_length:
                # can not be any more matches if this is satisfied.
                # this line is added to avoid IndexError in the following line
                return resulting_postings

            if b[b_idx + 1][2] != 0 and a[a_idx][0] - b[b[b_idx + 1][2]][0] >= 0:
                b_idx = b[b_idx + 1][2]
            else:
                b_idx += 1

    return resulting_postings


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """

    print('running search on the queries...')

    # create / wipe the results file before we start handling the queries
    open(results_file, 'w').close()

    with open(dict_file, 'rb') as read_dict:
        # We are able to read the full dictionary into memory
        # The dictionary is structured as * term_id : (doc_freq, file_offset)
        dictionary = pickle.load(read_dict)

    with open('term_conversion.txt', 'rb') as read_term_converter:
        # term (str) -> term id (int, 4 bytes)
        term_to_term_id = pickle.load(read_term_converter)

    """with open('document_lengths.txt', 'rb') as read_lengths:
        number_of_docs = pickle.load(read_lengths)
        documents_lengths = pickle.load(read_lengths)"""

    with open(queries_file, 'r') as queries:
        all_queries = queries.readlines()

    for q in all_queries:

        matches = re.findall(r'\"(.+?)\"', q)  # match text between two quotes
        for m in matches:
            match = []
            for word in m.split():
                match.append(normalize_token(word))

            q = q.replace('\"%s\"' % m, '%s' % "%".join(match))

        q = q.split()

        for idx, term in enumerate(q):
            print(term)
            if not '%' in term and term != 'AND':
                q[idx] = normalize_token(term)
            print(q[idx])

        if 'AND' in q:
            # treat like a boolean query

            first_AND_idx = q.index('AND')
            first_posting_list = search_term(q[first_AND_idx - 1], dictionary, term_to_term_id)
            second_posting_list = search_term(q[first_AND_idx + 1], dictionary, term_to_term_id)

            print(first_posting_list)
            print(second_posting_list)

            result = merge_postings(first_posting_list, second_posting_list)

            print(result)
            print(f'first list length = {len(first_posting_list)}\nsecond list length = {len(second_posting_list)}')
            print(f'result len {len(result)}')


def usage():
    print("usage: " +
          sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
