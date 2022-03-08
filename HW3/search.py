#!/usr/bin/python3
import pickle
import re
import nltk
import sys
import getopt


def retrieve_postings_list(dictionary, term_id):
    """
    Takes a term id and retrieves its posting list by using the dictionary to find the offset
    in the file the posting list was written to. Returns said postings list.
    """
    with open(postings_file, 'rb') as read_postings:
        reader_offset = dictionary[term_id][1]
        read_postings.seek(reader_offset)
        return pickle.load(read_postings)


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    with open(dict_file, 'rb') as read_dict:
        # We are able to read the full dictionary into memory
        # The dictionary is structured as - term_id : (doc_freq, file_offset)
        dictionary = pickle.load(read_dict)

    with open('term_conversion.txt', 'rb') as read_term_converter:
        term_to_term_id = pickle.load(read_term_converter)  # term (str) -> term id (int, 4 bytes)
        term_id_to_term = pickle.load(read_term_converter)  # term id (int, 4 bytes) -> term (str)

    test_id = term_to_term_id['the']
    print(term_id_to_term[test_id])
    print(retrieve_postings_list(dictionary, test_id))













### END OF FILE. RANDOM STUFF BELOW ###


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
