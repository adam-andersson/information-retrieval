#!/usr/bin/python3
import math
import os
import pickle
import time
import nltk
import sys
import getopt
import csv


PORTER_STEMMER = nltk.stem.porter.PorterStemmer()
STOP_WORDS = set(nltk.corpus.stopwords.words('english') + [".", ",", ";", ":"])

DATAFRAME_PROCESSED_FILEPATH = 'dataframe_processed.csv'
DOCUMENT_LENGTHS_FILEPATH = 'document_lengths.txt'
TERM_CONVERSION_FILEPATH = 'term_conversion.txt'

PREPROCESS_FILE = True
WRITE_INDEX_TO_FILE = True
USE_STEMMING = False


def create_ngram(sentence, n):
    """
    takes a string (sentence) and an integer n.
    constructs and returns an array of the string's n-grams.

    Use a window sliding technique to iteratively take the characters between index i and i+4 for all i s.t.
    we start with left side of window at i = 0, and end when right side of window at i = <idx of last character>
    """
    return [sentence[i:i + n] for i in range(len(sentence) - n + 1)]


def add_skip_ptrs(posting_list, length_of_posting_list):
    """
    Takes a list of tuples [(doc_id, doc_freq), (doc_id, doc_freq), ...]
    and returns a list of triples [(doc_id, doc_freq, index_of_skip), (doc_id, doc_freq, 0), ...]
    where index_of_skip is the index of the pointers destination in the list, and 0 if this posting does not have
    a skip pointer.
    """
    postings_list_with_skip_ptr = []

    skips_to_add = math.floor(math.sqrt(length_of_posting_list))
    skip_distance = math.floor(length_of_posting_list / skips_to_add)

    position_index = 0
    for key, value in posting_list.items():
        postings_list_with_skip_ptr.append([key, len(value), value, 0])

        if position_index % skip_distance == 0 and position_index != length_of_posting_list - 1 \
                and position_index + skip_distance < length_of_posting_list:
            postings_list_with_skip_ptr[-1][3] = position_index + skip_distance

        position_index += 1

    return postings_list_with_skip_ptr


def calculate_tf(term_frequency):
    return 1 + math.log10(term_frequency)


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding

    # removes leading and trailing non-alphanumeric characters
    token_length = len(token)
    l_idx = 0
    r_idx = token_length - 1

    for i in range(token_length):
        if token[i].isalnum():
            l_idx = i
            break

    for i in range(token_length - 1, 0, -1):
        if token[i].isalnum():
            r_idx = i
            break

    token = token[l_idx: r_idx + 1]

    # currently not using any stemming due to the time complexity of this operation
    if USE_STEMMING:
        token = PORTER_STEMMER.stem(token)  # porter-stemming

    return token


def normalize_words_in_list(list_of_words):
    return [normalize_token(token) for token in list_of_words]


def create_positional_index(content, document_id, term_id, term_to_term_id, term_id_to_term,
                            dictionary, postings_list, document_weights):
    """
    Create a postings list with positional indices. Goal is to have a dictionary where
    we have a term_id as key:
    dict[term_id] = doc_id:[54, 1337], doc_id: [123, 456, 789]
    """
    positional_idx = 0
    for token in content:
        positional_idx += 1

        if token not in term_to_term_id:
            # if it is the first time we see this term, we add it to our dictionaries of terms and term ids
            term_to_term_id[token] = term_id
            term_id_to_term[term_id] = token
            term_id += 1

        tokens_term_id = term_to_term_id[token]

        if tokens_term_id not in dictionary:
            # first time seeing it, so it has only been seen in the current document (i.e. doc freq = 1)
            dictionary[tokens_term_id] = 1

            postings_list[tokens_term_id] = {document_id: [positional_idx]}
            # initialise the dictionary that maps doc_ids to positions.

            document_weights[tokens_term_id] = 1
        else:
            # first time seeing this term for this document
            if document_id not in postings_list[tokens_term_id]:
                dictionary[tokens_term_id] += 1  # only increment for first occurrence in each document

                # since we process the documents in a sorted order, we can always append new documents to
                # the list and it will still be in a sorted order.
                postings_list[tokens_term_id][document_id] = [positional_idx]

                document_weights[tokens_term_id] = 1

            else:
                # if we have already seen this token in this posting already,
                # then we should add the current position to the list.
                postings_list[tokens_term_id][document_id].append(positional_idx)

                # this dictionary is used for storing length of documents, initialised to 1
                document_weights[tokens_term_id] += 1

    return term_id


def calculate_document_weight(document_weight, out_dictionary, document_id):
    # for every document, the weighted length of document is calculated for use when processing search queries.
    doc_wt_sum = 0
    for value in document_weight.values():
        tf_doc = calculate_tf(value)
        doc_wt_sum += tf_doc ** 2
    out_dictionary[document_id] = doc_wt_sum


def pre_process_file(in_file_path):
    """
    Takes the file path to a .csv file, reads this file and converts it to a Pandas dataframe. Then writes this
    dataframe to a file for use when indexing.
    """

    # increase maximum field size to solve the following error:
    # _csv.Error: field larger than field limit (131072)
    csv.field_size_limit(sys.maxsize)

    csvreader = csv.reader(open(in_file_path, 'r'))
    header = next(csvreader)

    csvreader = list(csvreader)

    df = []
    for row in csvreader:
        # The regexp tokenization is benchmarked to be much faster than what was implemented before:
        # src: https://towardsdatascience.com/benchmarking-python-nlp-tokenizers-3ac4735100c5

        tokenized_content = nltk.regexp_tokenize(row[2], pattern='\s+', gaps=True)

        normalized_content = normalize_words_in_list(tokenized_content)

        df.append([int(row[0]), normalized_content])  # add doc id and normalized & tokenized content fields

    with open(DATAFRAME_PROCESSED_FILEPATH, 'w') as df_file:
        write = csv.writer(df_file)
        write.writerow([header[0], header[2]])  # write the header field to the file.
        write.writerows(df)  # write the doc_id, processed content fields to the file.

    print(f'Wrote the processed dataframe to file.')
    return df


def open_processed_file(file_path=DATAFRAME_PROCESSED_FILEPATH):

    # increase maximum field size to solve the following error:
    # _csv.Error: field larger than field limit (131072)
    csv.field_size_limit(sys.maxsize)

    csvreader = csv.reader(open(file_path, 'r'))
    header = next(csvreader)

    df = list(csvreader)
    for i in range(len(df)):
        df[i][0] = int(df[i][0])

    return df


def build_index(in_file, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """

    # Wipe all contents from the files before running the code. Because we are appending (open with 'ab')
    # dictionaries from every block, we want to start from clean files.
    if WRITE_INDEX_TO_FILE:
        open(out_dict, 'w').close()
        open(out_postings, 'w').close()

    df = pre_process_file(in_file) if PREPROCESS_FILE else open_processed_file()

    ### START OF INDEXING ###

    number_of_documents = len(df)

    # Dictionaries for 1-grams
    term_to_term_id = {}
    term_id_to_term = {}
    dictionary = {}
    postings_list = {}
    documents_lengths = {}

    # create unique term id's that are incremented for every NEW word we discover in the full corpus.
    term_id = 1

    already_indexed_doc = []

    previous_time = time.time()
    currently_process_document_idx = 0

    print(f'Creating index ...')
    for document_id, content in df:
        if (currently_process_document_idx + 1) % 100 == 0:
            latest_time = time.time()

            print(f'Currently done with {currently_process_document_idx + 1}/{number_of_documents} docs \n'
                  f'These docs took: {latest_time - previous_time}')

            previous_time = latest_time

        # dictionary that keeps track of every terms frequency in this specific document
        # this is later converted to a sum of weighted tf^2 for use in search.py
        document_weights = {}

        if document_id in already_indexed_doc:
            print('This document have already been indexed')
            continue  # skip this document by going to the next iteration in the for loop

        already_indexed_doc.append(document_id)  # keep track of all document id that have been indexed already

        term_id = create_positional_index(content, document_id, term_id, term_to_term_id, term_id_to_term,
                                          dictionary, postings_list, document_weights)

        calculate_document_weight(document_weights, documents_lengths, document_id)
        currently_process_document_idx += 1

    """
    dictionary      ->  term_id          : number_of_documents_term_appears_in, postings_list_position_in_file
    postings_list   ->  [[document_id_1, terms_occurrences_in_document, <pos_1, pos_2, ...>, skip_ptr_idx]
                         [document_id_2, terms_occurrences_in_document, <pos_1, pos_2, ...>, 0]
                         ...]
    """

    if WRITE_INDEX_TO_FILE:
        with open(out_postings, 'wb') as write_postings:
            for term_id, posting_list in postings_list.items():
                skip_list = add_skip_ptrs(posting_list, len(posting_list))
                writer_position = write_postings.tell()

                pickle.dump(skip_list, write_postings)

                # every term_id in the dictionary will be a tuple of (doc_frequency, writer offset)
                dictionary[term_id] = (dictionary[term_id], writer_position)

        with open(out_dict, 'wb') as write_dict:
            pickle.dump(dictionary, write_dict)

        with open(DOCUMENT_LENGTHS_FILEPATH, 'wb') as write_lengths:
            pickle.dump(number_of_documents, write_lengths)
            pickle.dump(documents_lengths, write_lengths)  # store LENGTH[N] for future normalization

        with open(TERM_CONVERSION_FILEPATH, 'wb') as write_term_converter:
            # term (str) -> term id (int, 4 bytes)
            pickle.dump(term_to_term_id, write_term_converter)
            pickle.dump(term_to_term_id, write_term_converter)


def usage():
    print("usage: " + sys.argv[0] + " -i csv-of-documents -d dictionary-file -p postings-file")


input_csv = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        input_csv = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_csv is None or output_file_postings is None or output_file_dictionary is None:
    usage()
    sys.exit(2)

build_index(input_csv, output_file_dictionary, output_file_postings)
