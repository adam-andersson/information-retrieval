#!/usr/bin/python3
import bisect
import math
import os
import pickle
import re
import nltk
import sys
import getopt

sys.setrecursionlimit(
    100000)  # had to set recursion limit since some linked lists are long and leads to a lot of recursion

"""nltk.download('reuters')
nltk.download('punkt')
nltk.download('stopwords')"""

PORTER_STEMMER = nltk.stem.porter.PorterStemmer()
STOP_WORDS = set(nltk.corpus.stopwords.words('english') + [".", ",", ";", ":"])
NUMBER_OF_BLOCKS = 10


class Posting:
    def __init__(self, data):
        self.doc_id = data
        self.next = None
        self.skip = None

    def __repr__(self):
        return str(self.doc_id) + str(f' ({self.skip.doc_id})') if self.skip is not None else str(self.doc_id)


class PostingList:
    def __init__(self):
        self.head = None
        self.length = 1

    def add_first(self, node):
        node.next = self.head
        self.head = node

    def convert_to_linked_list(self, list_of_postings, number_of_postings):
        """
        Converts a list (array) to a linked list. A linked list is a head node (posting), with a NEXT pointer
        to another node (posting), which in turn have a NEXT pointer to the next posting etc.
        """
        self.length = number_of_postings
        current_node = self.head
        for posting_doc_id in list_of_postings:
            current_node.next = Posting(posting_doc_id)
            current_node = current_node.next

    def sortedMerge(self, a, b):
        """
        Merges two sorted linked lists. Since the posting lists from two different blocks can never have the
        same document id, there will be no duplicates as a result of this. Hence, it is the union between
        the a list and b list, and the intersection of these lists are none.
        """
        # Base cases
        if a is None:
            return b
        elif b is None:
            return a

        # Pick either a or b, and recur
        if a.doc_id <= b.doc_id:
            result = a
            result.next = self.sortedMerge(a.next, b)
        else:
            result = b
            result.next = self.sortedMerge(a, b.next)

        return result

    def add_skip_ptr(self, curr_node, skip_distance, curr_idx=0, looking_for_next=False):
        """
        Add skip pointers in a linked lists recursively. Parameters: a current node, the distance between every
        skip pointer, and an index and a boolean that is managed during recursion.

        The main intuition behind the method is to index all nodes during traversal and if the index modulo the
        distance between skip pointers is 0, then we place a skip pointer here. The skip pointer is directed
        to the next node eligible for a skip pointer.
        """

        result = curr_node

        if looking_for_next:
            # if curr_idx is evenly divided by skip_distance, we want to add a skip pointer to this node
            if curr_idx % skip_distance == 0:
                return result
            else:
                if result is None or result.next is None:
                    return None
                else:
                    # iterate deeper (if not and end of list) to find where to put the pointer
                    return self.add_skip_ptr(result.next, skip_distance, curr_idx + 1, looking_for_next)
        else:
            if curr_idx % skip_distance == 0:
                looking_for_next = True
                result.skip = self.add_skip_ptr(result.next, skip_distance, curr_idx + 1, looking_for_next)

        # main loop
        if result.next is not None:
            self.add_skip_ptr(result.next, skip_distance, curr_idx + 1, False)

    def __iter__(self):
        """
        This is used for iteration of the linked lists, use case: for node in PostingList {}.
        """
        node = self.head
        while node is not None:
            yield node
            node = node.next

    def __repr__(self):
        """
        This is used to print the posting list, calling print(instance of PostingList()) prints the length of the
        postings list followed by all the nodes in the list joined together by arrows,
        representing the next pointer's direction.
        """
        node = self.head
        nodes = ['len' + str(self.length)]
        while node is not None:
            nodes.append(str(node))
            node = node.next
        nodes.append("None")
        return " -> ".join(nodes)


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding
    token = PORTER_STEMMER.stem(token)  # porter-stemming
    return token


def merge_postings(listA, listB, length):
    """
    Driver function for merging two sorted posting lists, A and B.
    """
    merged_postings = PostingList()
    merged_postings.length = length
    merged_postings.head = merged_postings.sortedMerge(listA.head, listB.head)

    return merged_postings


def merge_dict(prev_dictionary, to_merge_dictionary):
    """
    Merges two dictionaries by copying all entries in both dictionaries, for entries with the same key,
    the new value (doc freq) is the addition between the doc frequencies from the previous two dictionaries.
    """
    merged_dict = {**prev_dictionary, **to_merge_dictionary}
    for key, value in merged_dict.items():
        if key in prev_dictionary and key in to_merge_dictionary:
            merged_dict[key] = prev_dictionary[key] + to_merge_dictionary[key]
    return merged_dict


def merge_posting_dict(prev_posting_dict, to_merge_posting_dict):
    """
    Merges two posting list dictionaries by copying all entries in both dictionaries,
    for entries where the key is the same in both dictionaries, their posting lists are merged separately.
    """
    merged_posting_dict = {**prev_posting_dict, **to_merge_posting_dict}
    for term_id, posting_list in merged_posting_dict.items():
        if term_id in prev_posting_dict and term_id in to_merge_posting_dict:
            # There can never be duplicates in these posting dictionaries since they have all processed different docs.
            # Hence, the merged list will be of length x+y.
            length = prev_posting_dict[term_id].length + to_merge_posting_dict[term_id].length
            merged_posting_dict[term_id] = merge_postings(prev_posting_dict[term_id], to_merge_posting_dict[term_id], length)
    return merged_posting_dict


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

    term_to_term_id = {}    # term (str) -> term id (int, 4 bytes)
    term_id_to_term = {}    # term id (int, 4 bytes) -> term (str)
    term_id = 1  # we keep a global term id that we will assign to tokens when processing them

    all_documents = [int(f) for f in os.listdir(in_dir)]

    number_of_docs = len(all_documents)
    block_size = int(number_of_docs / NUMBER_OF_BLOCKS) + 1

    for block_number in range(NUMBER_OF_BLOCKS):
        block = all_documents[block_number * block_size: (1 + block_number) * block_size]

        # print(f'Block Number: {block_number} \nBlock includes doc id: \n{block}')

        block_dictionary = {}  # term_id -> document frequency of term
        block_postings = {}  # term_id -> posting[0] -> posting[1] ...

        if block_number == NUMBER_OF_BLOCKS - 1:   # if it is the very last block
            # Add a special entry that has a list of ALL postings.
            # It is later used for handling some "NOT" queries.
            token = 'all_documents_combined'
            term_to_term_id[token] = term_id
            term_id_to_term[term_id] = token
            # the document frequency of this term is nil, since it should never appear in any document
            block_dictionary[term_id] = 0
            block_postings[term_id] = sorted(all_documents)
            term_id += 1

        for doc_id in block:
            with open(os.path.join(in_dir, str(doc_id)), 'r') as doc_open:
                doc_text = doc_open.read()

            sentences = nltk.sent_tokenize(doc_text)

            processed_document = []
            for s in sentences:
                words = nltk.word_tokenize(s)

                # case-fold all word tokens, then porter-stem the word
                processed_document.append([normalize_token(token) for token in words])

                # This line was previously used when we also deleted stop words
                # [...].append([normalize_token(token) for token in words if token.lower() not in STOP_WORDS])

            for sentence in processed_document:
                for token in sentence:
                    if token not in term_to_term_id:
                        term_to_term_id[token] = term_id
                        term_id_to_term[term_id] = token
                        term_id += 1

                    tokens_term_id = term_to_term_id[token]

                    if tokens_term_id not in block_dictionary:
                        # first time seeing it, so it has only been seen in this document (i.e. doc freq (block) = 1)
                        block_dictionary[tokens_term_id] = 1
                        block_postings[tokens_term_id] = [doc_id]
                    else:
                        if doc_id not in block_postings[tokens_term_id]:  # first time seeing this term for this doc
                            block_dictionary[tokens_term_id] += 1  # only increment for first occurrence in each docu

                            # bisect is a built-in module. Uses binary search [O(log n)] to
                            # insert element into a sorted list.
                            bisect.insort(block_postings[tokens_term_id], doc_id)

        for term, terms_postings in block_postings.items():
            posting_list = PostingList()
            posting_list.add_first(Posting(terms_postings[0]))
            number_of_postings = len(terms_postings)

            if number_of_postings > 1:
                posting_list.convert_to_linked_list(terms_postings[1:], number_of_postings)
            block_postings[term] = posting_list  # overwrite the previous list representation with a linked list

        with open(out_dict, 'ab') as write_dict:  # using 'ab' appends this dump to previous dump we have done
            pickle.dump(block_dictionary, write_dict)

        with open(out_postings, 'ab') as write_postings:
            pickle.dump(block_postings, write_postings)

        print(f'Done with processing and writing block {block_number} / {NUMBER_OF_BLOCKS}')

    print("... done with reading / writing blocks")

    with open('term_conversion.txt', 'wb') as term_conversion:
        pickle.dump(term_to_term_id, term_conversion)
        pickle.dump(term_id_to_term, term_conversion)

    merged_postings = {}
    read_postings = open(out_postings, 'rb')
    for _ in range(NUMBER_OF_BLOCKS):
        to_merge_postings = pickle.load(read_postings)
        merged_postings = merge_posting_dict(merged_postings, to_merge_postings)
        print(f'Done with merging block (0 -> {_}) and {_ + 1}')

    read_postings.close()

    merged_dictionary = {}
    # need to open and keep open for pickle.load() to remember what have been read
    read_dict = open(out_dict, 'rb')
    for _ in range(NUMBER_OF_BLOCKS):
        to_merge_dictionary = pickle.load(read_dict)
        merged_dictionary = merge_dict(merged_dictionary, to_merge_dictionary)
    read_dict.close()

    max_length = 0
    max_term_id = 0

    with open(out_postings, 'wb') as write_postings:
        for term_id, posting_list in merged_postings.items():
            if posting_list.length > max_length:
                max_length = posting_list.length
                max_term_id = term_id

            number_of_skips = math.sqrt(posting_list.length)
            skip_distance = math.floor(posting_list.length / number_of_skips)
            if skip_distance > 1:
                posting_list.add_skip_ptr(posting_list.head, skip_distance)

            writer_position = write_postings.tell()
            pickle.dump(merged_postings[term_id], write_postings)
            # every term_id in the dictionary will be a tuple of (doc_frequency, writer offset)
            merged_dictionary[term_id] = (merged_dictionary[term_id], writer_position)

    print(f'Maximum length posting list is {max_length} long. It is the word {term_id_to_term[max_term_id]}.')

    with open(out_dict, 'wb') as write_dict:
        pickle.dump(merged_dictionary, write_dict)


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        input_directory = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
