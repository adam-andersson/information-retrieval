#!/usr/bin/python3
import math
import pickle
import re
import nltk
import sys
import getopt
from heapq import heappop, heappush, heapify

PORTER_STEMMER = nltk.stem.porter.PorterStemmer()


class TrackScore:
    def __init__(self, doc_id, score):
        self.document_id = doc_id
        self.score = score

    def __str__(self):
        # can uncomment the last lines for debugging of the scores.
        return str(self.document_id) + " (" + str(self.score) + ")"

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


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding

    # currently not using any stemming due to the time complexity of this operation
    #   token = PORTER_STEMMER.stem(token)  # porter-stemming

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


def search_dictionary(term_to_search, dictionary, term_to_term_id):
    """
    Searches a term (str) in the dictionary to find this term's: document frequency and
    the byte pointer to the term's posting list in the postings file.
    """
    if term_to_search not in term_to_term_id:
        return []  # if the query term does not exist in dictionary, return an empty posting list

    term_id = term_to_term_id[term_to_search]
    return dictionary[term_id]


def calculate_tf(term_frequency):
    return 1 + math.log10(term_frequency)


def calculate_idf(number_of_docs, document_frequency):
    return math.log10(number_of_docs / document_frequency)


def cosine_normalize_factor(weight_squared_sum):
    return 1 / math.sqrt(weight_squared_sum)


def merge_boolean_query(a, b, save_both_docs=False):
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
            if save_both_docs:
                resulting_postings.append(b[b_idx])
            a_idx += 1

        elif a[a_idx][0] < b[b_idx][0]:
            if a_idx + 1 == a_length:
                # can not be any more matches if this is satisfied.
                # this line is added to avoid IndexError in the following line
                return resulting_postings

            if a[a_idx + 1][3] != 0 and b[b_idx][0] - a[a[a_idx + 1][3]][0] >= 0:
                # use skip pointer
                a_idx = a[a_idx + 1][3]
            else:
                a_idx += 1

        elif a[a_idx][0] > b[b_idx][0]:
            if b_idx + 1 == b_length:
                # can not be any more matches if this is satisfied.
                # this line is added to avoid IndexError in the following line
                return resulting_postings

            if b[b_idx + 1][3] != 0 and a[a_idx][0] - b[b[b_idx + 1][3]][0] >= 0:
                # use skip pointer
                b_idx = b[b_idx + 1][3]
            else:
                b_idx += 1

    return resulting_postings


def handle_phrase_query(phrase_search_term_joined, dictionary, term_to_term_id):
    """
    Driver function for converting a %-joined phrase term on the form "hi%my%name" into a resulting posting
    list containing all the documents where this phrase was written (the 2 or 3 words happened in order).
    """
    postings = []
    term_frequencies = []

    for term in phrase_search_term_joined.split('%'):
        dictionary_term = search_dictionary(term, dictionary, term_to_term_id)
        posting_term = search_term(term, dictionary, term_to_term_id)

        if not dictionary_term or not posting_term:
            return []

        postings.append(posting_term)
        term_frequencies.append(dictionary_term[0])

    sorted_postings_list = [x for _, x in sorted(zip(term_frequencies, postings))]

    result = []

    if len(sorted_postings_list) == 2:
        result = phrase_intersection(sorted_postings_list[0], sorted_postings_list[1])
    elif len(sorted_postings_list) == 3:
        intermediate_intersection = phrase_intersection(sorted_postings_list[0], sorted_postings_list[1])
        result = phrase_intersection(intermediate_intersection, sorted_postings_list[2])
    else:
        print(f'Invalid length of phrase.')

    return result


def phrase_intersection(p_1, p_2):
    """
    Proximity intersection of posting lists p1 and p2 where the two words appear at the
    correct distance (distance == 1 for phrase query) from each other.
    """
    merged_postings = merge_boolean_query(p_1, p_2, True)

    result_posting = []

    i = 0
    while i < len(merged_postings):
        document_temp_list = [merged_postings[i][0], 0, [], 0]
        this_doc_is_relevant = False

        for position_x in merged_postings[i][2]:
            for position_y in merged_postings[i + 1][2]:
                if position_x == position_y - 1:
                    document_temp_list[2].append(position_y)
                    this_doc_is_relevant = True

        if this_doc_is_relevant:
            result_posting.append(document_temp_list)

        i += 2  # want to increment i by two every iteration.

    return result_posting


def write_results_to_file(results_file, heap, number_of_results=None):
    """
    Takes a file path and a heap of (TrackScore) objects and writes them in order of decreasing score to the file.
    """
    if number_of_results:
        # only write the top X results, or less if there isn't 10 good matches.
        number_of_results = number_of_results if len(heap) > number_of_results else len(heap)
    else:
        number_of_results = len(heap)

    out_string = " ".join([str(heappop(heap)) for _ in range(number_of_results)]) + '\n'

    with open(results_file, 'a') as write_result:
        write_result.write(out_string)


def add_term_freq_to_dictionary(posting_list, dictionary, initial_creation=False):
    """
    Adds the term/phrase frequency in a document to a dictionary for use when ranking boolean queries.
    output: dictionary -> doc_id_1: [3, 13], doc_id_2: [11, 12]. Which would mean that in doc_id_1, the first term
    appeared 3 times and the second term or phrase 13 times in the document.
    """

    for posting in posting_list:
        term_freq_in_doc = len(posting[2])
        if posting[0] not in dictionary and initial_creation:
            dictionary[posting[0]] = [term_freq_in_doc]
        elif posting[0] in dictionary and not initial_creation:
            dictionary[posting[0]].append(term_freq_in_doc)

    return dictionary


def handle_ranked_retrieval(query, dictionary, term_to_term_id, number_of_docs):
    """
    Takes a query and calculates tf-idf for this query in all documents that contains this term.
    Returns a dictionary containing all documents that appeared as key, and the sum of all tf-idf s for each
    document as value.
    """
    scores_pre_normalize = {}
    sum_weight_q = 0

    for q_term in query:

        # --- IDF (QUERY) --- #
        if q_term in term_to_term_id:
            term_id = term_to_term_id[q_term]
            doc_freq = dictionary[term_id][0]

            # idf query -> parameters: total number of documents and document frequency
            idf_qt = calculate_idf(number_of_docs, doc_freq)
        else:
            # the idf for the query term is set to 0 if it appears in NO documents
            idf_qt = 0

        # --- TERM FREQUENCY (QUERY) --- #
        term_freq_qt = query.count(q_term)
        tf_qt = calculate_tf(term_freq_qt)

        # --- TF x IDF (QUERY) --- #
        weight_qt = tf_qt * idf_qt

        # add this weight (squared) to the total squared weight of this query. This is used in cosine normalization
        sum_weight_q += weight_qt ** 2

        # in case of no posting list belonging to query term t, this will always return an empty list "[]"
        # which will be caught in the following if-statement.
        posting_t = search_term(q_term, dictionary, term_to_term_id)

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

    return scores_pre_normalize, sum_weight_q


def filter_term_freq(dictionary, results):
    """
    Updates the document term frequency dictionary to only include the documents that are still matching
    the boolean query and keeping track of the most frequent yet.
    """
    new_dict = {}
    global_max_freq = 1
    for result in results:
        new_dict[result[0]] = dictionary[result[0]]

        max_freq = max(dictionary[result[0]])
        if max_freq > global_max_freq:
            global_max_freq = max_freq

    del dictionary

    new_dict['highest_occ'] = global_max_freq
    return new_dict


def handle_boolean_query(query, dictionary, term_to_term_id, boolean_query=False, merged_posting_list=None,
                         document_term_freq=None):
    """
    Gets called if the query is a boolean query. Takes a list of query terms, and is the driver function for calling
    functions that process phrases, retrieve posting lists and merge posting lists. It is called recursively until
    all of the query have been processed.
    """
    if document_term_freq is None:
        document_term_freq = {}

    if merged_posting_list is None:
        merged_posting_list = []

    if 'AND' in query or boolean_query:
        print("Treat all of the query as a boolean query")

        first_AND_idx = query.index('AND')  # raises ValueError if not found.

        if len(query) < 2:
            # error in the input. just return the results this far / or an empty list as it won't break anything.
            print(f'Error in the input.')
            return merged_posting_list

        right_search_term = query[first_AND_idx + 1]

        if not merged_posting_list:
            # in case this is the very first query term/phrase in this query.

            left_search_term = query[first_AND_idx - 1]

            query.pop(0)  # remove the left search term from the query

            if '%' in left_search_term:
                merged_posting_list = handle_phrase_query(left_search_term, dictionary, term_to_term_id)
            else:
                merged_posting_list = search_term(left_search_term, dictionary, term_to_term_id)

            add_term_freq_to_dictionary(merged_posting_list, document_term_freq, True)

        if '%' in right_search_term:
            right_posting_list = handle_phrase_query(right_search_term, dictionary, term_to_term_id)
        else:
            right_posting_list = search_term(right_search_term, dictionary, term_to_term_id)

        add_term_freq_to_dictionary(right_posting_list, document_term_freq)

        query.pop(0)  # remove the 'AND' term from the query
        query.pop(0)  # remove the right search term from the query

        result_postings = merge_boolean_query(merged_posting_list, right_posting_list)

        document_term_freq = filter_term_freq(document_term_freq, result_postings)

        print(f'REMAINING QUERY: {query}')
        # if we still have not gone through all of the query, we recur.
        if query:
            return handle_boolean_query(query, dictionary, term_to_term_id, True, result_postings, document_term_freq)
        else:
            return result_postings, document_term_freq

    else:
        print(f'Error in input.')
        return []


def boolean_and_freq_to_score(frequency_vector, priority_constant=6):
    """
    Uses the standard deviation to promote documents that contains all search terms/phrases multiple times.
    Tries to find a balance between total number of occurrences and the spread of said occurrences.
    The priority constant can be adjusted.
    Lower   -> Gives better score to documents with equal distributions.
    Higher  -> Gives better score to documents with high total number of occurrences.
    """
    # TODO: Find a good balance on how to score the boolean queries.

    arithmetic_average = sum(frequency_vector) / len(frequency_vector)

    deviation_sum = 0
    for val in frequency_vector:
        deviation_sum += (int(val) - arithmetic_average) ** 2

    std_dev_sq = (deviation_sum/len(frequency_vector))

    deviation_score = std_dev_sq**(1/priority_constant)

    score = sum(frequency_vector) / deviation_score

    print(f'SCORE: {score}')

    return score


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

    with open('document_lengths.txt', 'rb') as read_lengths:
        number_of_docs = pickle.load(read_lengths)
        documents_lengths = pickle.load(read_lengths)

    with open(queries_file, 'r') as queries:
        all_queries = queries.readlines()

    for q in all_queries:

        matches = re.findall(r'\"(.+?)\"', q)  # match text between two quotes
        for m in matches:
            match = []
            for word in m.split():
                match.append(normalize_token(word))

            # in case of a phrase query; concatenate the words in the phrase with a % between them.
            q = q.replace('\"%s\"' % m, '%s' % "%".join(match))

        q_split = q.split()
        for idx, term in enumerate(q_split):
            q_split[idx] = normalize_token(term) if term != 'AND' else 'AND'

        # we know that the query should be treated as a boolean query if it includes quotes or the "AND" operator.
        is_boolean_query = len(matches) != 0 or 'AND' in q_split

        results_heap = []
        heapify(results_heap)

        if is_boolean_query:
            search_results, result_frequencies = handle_boolean_query(q_split, dictionary, term_to_term_id)

            for result in search_results:
                # TrackScore is a custom class that is used to be able to define our own definition of "<" and "="
                # between objects and also the string representation of such objects.
                score = boolean_and_freq_to_score(result_frequencies[result[0]])
                new_score = TrackScore(result[0], score)

                # this max-heap have the score of ALL documents, uses the heapq (min-heap) module but turns into a
                # max-heap by changing the definitions of lt and eq with TrackScore class.
                heappush(results_heap, new_score)
        else:
            scores_pre_normalize, sum_weight_q = handle_ranked_retrieval(q_split, dictionary, term_to_term_id,
                                                                         number_of_docs)

            for key, value in scores_pre_normalize.items():
                # note: the document lengths was calculated during indexing and is used from a dictionary during search.

                normalized_score = value * cosine_normalize_factor(sum_weight_q) * \
                                   cosine_normalize_factor(documents_lengths[key])

                # TrackScore is a custom class that is used to be able to define our own definition of "<" and "="
                # between objects and also the string representation of such objects.
                new_score = TrackScore(key, normalized_score)

                # this max-heap have the score of ALL documents, uses the heapq (min-heap) module but turns into a
                # max-heap by changing the definitions of lt and eq with TrackScore class.
                heappush(results_heap, new_score)

        write_results_to_file(results_file, results_heap)


### Handle input ###

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

if dictionary_file is None or postings_file is None or file_of_queries is None or file_of_output is None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
