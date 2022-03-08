#!/usr/bin/python3
import math
import os
import bisect
import pickle
import re
import nltk
import sys
import getopt

PORTER_STEMMER = nltk.stem.porter.PorterStemmer()
STOP_WORDS = set(nltk.corpus.stopwords.words('english') + [".", ",", ";", ":"])
NUMBER_OF_BLOCKS = 10


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding
    token = PORTER_STEMMER.stem(token)  # porter-stemming
    return token


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    # Wipe all contents from the files before running the code. Because we are appending (open with 'ab')
    # dictionaries from every block, we want to start from clean files.
    open(out_dict, 'w').close()
    open(out_postings, 'w').close()

    term_to_term_id = {}  # term (str) -> term id (int, 4 bytes)
    term_id_to_term = {}  # term id (int, 4 bytes) -> term (str)
    term_id = 1  # we keep a global term id that we will assign to tokens when processing them

    all_documents = [int(f) for f in os.listdir(in_dir)]
    all_documents.sort()    # TODO: Evaluate if it is OK to sort this. It makes the later implementations easier.

    dictionary = {}
    postings_list = {}

    for doc_id in all_documents:
        with open(os.path.join(in_dir, str(doc_id)), 'r') as doc_open:
            doc_text = doc_open.read()

        sentences = nltk.sent_tokenize(doc_text)

        processed_document = []
        for s in sentences:
            words = nltk.word_tokenize(s)

            # case-fold all word tokens, then porter-stem the word
            processed_document.append([normalize_token(token) for token in words])

        for sentence in processed_document:
            for token in sentence:
                if token not in term_to_term_id:
                    # if it is the first time we see this term, we add it to our dictionaries of terms and term ids
                    term_to_term_id[token] = term_id
                    term_id_to_term[term_id] = token
                    term_id += 1

                tokens_term_id = term_to_term_id[token]

                if tokens_term_id not in dictionary:
                    # first time seeing it, so it has only been seen in the current document (i.e. doc freq (block) = 1)
                    dictionary[tokens_term_id] = 1
                    postings_list[tokens_term_id] = [(doc_id, 1)]   # initialise term freq to 1 (2nd term)
                    # every posting in a postings list is a tuple (doc_id, term_freq)
                else:
                    # first time seeing this term for this doc
                    if doc_id != postings_list[tokens_term_id][-1][0]:
                        dictionary[tokens_term_id] += 1  # only increment for first occurrence in each docu

                        " This was used when not sorting the documents before starting to process them "
                        # bisect is a built-in module. Uses binary search [O(log n)] to
                        # insert element into a sorted list.
                        # bisect.insort(postings_list[tokens_term_id], (doc_id, 1))

                        postings_list[tokens_term_id].append((doc_id, 1))

                    else:
                        # if we have already seen this token in this posting already,
                        # then we should add to its term frequency.

                        postings_list[tokens_term_id][-1] = (postings_list[tokens_term_id][-1][0], postings_list[tokens_term_id][-1][1] + 1)

                        """
                        for i in range(len(postings_list[tokens_term_id])):
                            posting = postings_list[tokens_term_id][i]
                            if posting[0] == doc_id:
                                # can not modify a tuple, need to overwrite, hence:
                                postings_list[tokens_term_id][i] = (posting[0], posting[1] + 1)
                                break   # this can only happen once so we break when this happens
                                
                        """

    print("... done with reading / writing blocks")

    with open('term_conversion.txt', 'wb') as term_conversion:
        pickle.dump(term_to_term_id, term_conversion)
        pickle.dump(term_id_to_term, term_conversion)

    with open(out_postings, 'wb') as write_postings:
        for term_id, posting_list in postings_list.items():
            writer_position = write_postings.tell()
            pickle.dump(posting_list, write_postings)

            # every term_id in the dictionary will be a tuple of (doc_frequency, writer offset)
            dictionary[term_id] = (dictionary[term_id], writer_position)

    with open(out_dict, 'wb') as write_dict:
        pickle.dump(dictionary, write_dict)














### END OF FILE. RANDOM STUFF BELOW ###


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
