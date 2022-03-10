#!/usr/bin/python3
import bisect
import math
import pickle
import re
import nltk
import sys
import getopt
from heapq import heappop, heappush, heapify, nlargest, nsmallest, heapreplace
import time

PORTER_STEMMER = nltk.stem.porter.PorterStemmer()


class TrackScore:
    def __init__(self, doc_id, score):
        self.document_id = doc_id
        self.score = score

    def __str__(self):
        # can uncomment the last lines for debugging of the scores.
        return str(self.document_id)  # + " (" + str(self.score) + ")"

    def __lt__(self, other):
        """
        Override the normal less than function for our class. Since available heap implementations are min-heaps,
        this simple tricks turns it into a max-heap.
        """
        if self.score != other.score:
            return self.score > other.score
        else:
            # if two documents have the same relevance, then we sort them by document id instead (in increasing order)
            return self.document_id < other.document_id

    def __eq__(self, other):
        return self.score == other.score

    def __repr__(self):
        return str(self.score)


def write_results_to_file(results_file, heap, number_of_results=10):
    # only write the top X results, or less if there isn't 10 good matches.
    number_of_results = number_of_results if len(heap) > 10 else len(heap)

    out_string = " ".join([str(heappop(heap)) for _ in range(number_of_results)]) + '\n'

    with open(results_file, 'a') as write_result:
        write_result.write(out_string)


def retrieve_postings_list(dictionary, term_id):
    """
    Takes a term id and retrieves its posting list by using the dictionary to find the offset
    in the file the posting list was written to. Returns said postings list.
    """
    with open(postings_file, 'rb') as read_postings:
        reader_offset = dictionary[term_id][1]
        read_postings.seek(reader_offset)
        return pickle.load(read_postings)


def calculate_tf(term_frequency):
    return 1 + math.log10(term_frequency)


def calculate_idf(number_of_docs, document_frequency):
    return math.log10(number_of_docs / document_frequency)


def calculate_tf_idf(term_freq, term_idf):
    return (1 + math.log10(term_freq)) * term_idf


def cosine_normalize_factor(weight_squared_sum):
    return 1 / math.sqrt(weight_squared_sum)


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding
    token = PORTER_STEMMER.stem(token)  # porter-stemming
    return token


def search_term(term_to_search, dictionary, term_to_term_id):
    """
    Converts a term (str) to a posting list. Tries to first convert the term (str) to a term id (int) and
    then uses this term id to call a function that retrieves the posting list.
    """
    if term_to_search in term_to_term_id:
        term_id = term_to_term_id[term_to_search]
    else:
        return []    # if a query term does not exist, just return an empty posting list

    return retrieve_postings_list(dictionary, term_id)


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
        # The dictionary is structured as - term_id : (doc_freq, file_offset)
        dictionary = pickle.load(read_dict)

    with open('term_conversion.txt', 'rb') as read_term_converter:
        term_to_term_id = pickle.load(read_term_converter)  # term (str) -> term id (int, 4 bytes)

    with open('document_lengths.txt', 'rb') as read_lengths:
        number_of_docs = pickle.load(read_lengths)
        documents_lengths = pickle.load(read_lengths)  # read LENGTH[N] for use when normalizing

    with open(queries_file, 'r') as queries:
        all_queries = queries.readlines()

    for query in all_queries:
        query_terms = []
        split_q = query.split()

        for term in split_q:
            query_terms.append(normalize_token(term))

        scores_pre_normalize = {}
        sum_weight_q = 0

        for t in query_terms:

            # --- IDF (QUERY) --- #
            if t in term_to_term_id:
                term_id = term_to_term_id[t]
                doc_freq = dictionary[term_id][0]

                # idf query -> parameters: document frequency and total number of documents
                idf_qt = calculate_idf(number_of_docs, doc_freq)
            else:
                # the idf for the query term is set to 1 if it appears in NO documents
                # this is an effort to avoid division or logarithm with zero.
                # TODO: Evaluate if it is OK to set it to 0 or if another approach should be taken.
                idf_qt = 0

            # --- TERM FREQUENCY (QUERY) --- #
            term_freq_qt = query_terms.count(t)
            tf_qt = calculate_tf(term_freq_qt)

            # --- TF x IDF (QUERY) --- #
            weight_qt = calculate_tf_idf(tf_qt, idf_qt)

            # add this weight (squared) to the total squared weight of this query.
            sum_weight_q += weight_qt**2

            # in case of no posting list belonging to query term t, this will always return an empty list "[]"
            # which will be caught in the following if-statement.
            posting_t = search_term(t, dictionary, term_to_term_id)

            # if this is a search query term that we do not have in our dictionary
            # otherwise, the score contribution after multiplication will always be zero for this term.
            if posting_t:
                for posting in posting_t:
                    doc_id = posting[0]

                    if doc_id not in scores_pre_normalize:
                        scores_pre_normalize[doc_id] = 0

                    term_freq_td = posting[1]
                    tf_dt = calculate_tf(term_freq_td)

                    # accumulate the product of non-normalized wt_doc and wt_query for every document
                    # this will later be normalized using cosine normalization.
                    scores_pre_normalize[doc_id] += weight_qt * tf_dt

        lnc_ltc_heap = []
        heapify(lnc_ltc_heap)

        for key, value in scores_pre_normalize.items():
            # formula for cosine normalization of the score is:
            # [sum of all t in query: (wt*wt)] * [sum of all terms in document: tf_wt**2] *
            # [sum of all terms in query: wt**2]

            # note: the sum of all terms in document was calculated during indexing and is used
            # from a dictionary during search.

            normalized_score = value * cosine_normalize_factor(sum_weight_q) * \
                          cosine_normalize_factor(documents_lengths[key])

            new_score = TrackScore(key, normalized_score)

            # This max-heap have the score of ALL documents, this is not optimal for time complexity
            # TODO: Make the heap fixed size.
            heappush(lnc_ltc_heap, new_score)

        write_results_to_file(results_file, lnc_ltc_heap, 10)


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
