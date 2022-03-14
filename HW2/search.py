#!/usr/bin/python3
import pickle
import re
import nltk
import sys
import getopt

sys.setrecursionlimit(
    100000)  # had to set recursion limit since some linked lists are long and leads to a lot of recursion

OPERATORS = ["NOT", "AND", "OR"]
PRECEDENCE_DICT = {"NOT": 3, "AND": 2, "OR": 1}  # the precedence order for not, and, or.
PORTER_STEMMER = nltk.stem.porter.PorterStemmer()
STOP_WORDS = set(nltk.corpus.stopwords.words('english') + [".", ",", ";", ":"])
NUMBER_OF_BLOCKS = 10

with open('term_conversion.txt', 'rb') as read_term_converter:
    term_to_term_id = pickle.load(read_term_converter)  # term (str) -> term id (int, 4 bytes)
    term_id_to_term = pickle.load(read_term_converter)  # term id (int, 4 bytes) -> term (str)


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

    def or_merge(self, a, b):
        """
        This is the same as a merge between the two posting lists. We are looking for the union of two linked lists.
        This code will add all nodes from both lists, later we remove potential duplicates.
        Time Complexity: O(x+y)
        Inspiration for code: https://www.geeksforgeeks.org/merge-two-sorted-linked-list-without-duplicates/
        """
        result = None

        # Base cases
        if a is None:
            return b
        elif b is None:
            return a

        # Pick either a or b, and recur
        if a.doc_id <= b.doc_id:
            # we include also the "=" case, since we will remove duplicates later
            result = a
            result.next = self.or_merge(a.next, b)
        elif a.doc_id > b.doc_id:
            result = b
            result.next = self.or_merge(a, b.next)

        return result

    def remove_duplicates(self, head_node):
        """
        This method goes through a sorted linked list and removes all duplicates, postings that have the same
        document id. Time complexity is O(n), where n is the total number of nodes in the postings list.
        Inspiration for code: https://www.geeksforgeeks.org/merge-two-sorted-linked-list-without-duplicates/
        """
        current = head_node

        # if the list is completely empty
        if current is None:
            return

        # Traverse the list until we are at the last node
        while current.next is not None:
            if current.doc_id == current.next.doc_id:
                next_next = current.next.next
                del current.next
                current.next = next_next
            else:
                # Continue traversing only if we did NOT just remove a node
                current = current.next

    def and_merge(self, a, b):
        """
        This is the same as looking for the intersection of two linked lists.
        Time Complexity: O(x+y)
        """
        result = None

        # Base case. An AND operation always return null if one of the lists are empty
        if a is None or b is None:
            return None

        if a.doc_id == b.doc_id:
            # if the two postings are the same, it should (hopefully) not matter which one we choose to add to our list
            result = a
            result.next = self.and_merge(a.next, b)

        elif a.doc_id < b.doc_id:
            if a.next is None:
                return None
            # we only use the skip ptr if it gets us closer to the larger doc_id of b
            if a.skip is not None and b.doc_id - a.skip.doc_id >= 0:
                result = self.and_merge(a.skip, b)
            else:
                result = self.and_merge(a.next, b)

        elif a.doc_id > b.doc_id:
            if b.next is None:
                return None
            # we only use the skip ptr if it gets us closer to the larger doc_id of a
            if b.skip is not None and a.doc_id - b.skip.doc_id >= 0:
                result = self.and_merge(a, b.skip)
            else:
                result = self.and_merge(a, b.next)

        return result

    def and_not_merge(self, a, b):
        """
        This method takes the head node of two lists, a and b. The core intuition behind the method is:
        postingList(A) - postingList(B). Hence, all postings in a is iterated, and whenever a posting
        exists in both the a and b list, that posting is removed from a by changing the pointer of the previous node
        to skip the colliding posting.
        """
        head_a = a
        prev_a = None
        prev_skip = None

        # Base case. When b is None, we just return a.
        if b is None:
            return head_a

        while a is not None and a.next is not None:
            if a.doc_id == b.doc_id:
                if prev_a is None:
                    # this if statement would only apply if the very first postings of both lists match.
                    head_a = a.next
                    b = b.next

                # If the doc id's are the same, we manipulate the pointer of the
                # previous posting to the node after the current. Deciding the previous posting is a bit
                # tricky because we are using skip pointers, hence the below if-statement.

                # this if statement makes sure no previous skip ptr causes us to delete all
                # nodes between the skip start to the skip end.
                if prev_skip:
                    c = prev_skip
                    d = prev_skip
                    while c is not None and c.next is not None:
                        if c.doc_id == b.doc_id:
                            d.next = c.next  # set the previous posting's next to the current's next posting
                            a = d  # continue traversing from node a (= d (= first node before the collision))
                            break  # we are done with this while-loop within while-loop and break
                        else:
                            d = c
                            c = c.next  # continue traversing and remember last posting with var d.
                else:
                    if prev_a is None:
                        a = head_a
                    else:
                        prev_a.next = a.next  # set the previous posting's next to the current's next posting
                        a = a.next  # continue the forward traversal of the lists

            elif a.doc_id < b.doc_id:
                prev_skip = None
                prev_a = a

                # if this is the case, then we check if we can use the skip ptr or not.
                if a.skip is not None and b.doc_id - a.skip.doc_id >= 0:
                    prev_skip = a   # if we use the skip pointer, we remember where we skipped from.
                                    # "With great power comes great responsibility."
                    a = a.skip  # traverse forward using the skip pointer
                else:
                    a = a.next

            elif a.doc_id > b.doc_id:
                prev_skip = None
                prev_a = a

                if b.next is None:
                    break
                else:
                    b = b.next  # traverse forward in b's postings

        return head_a

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
        This is used to print the posting list, calling print(instance of PostingList()) prints
        all the nodes in the list with a whitespace between
        """
        node = self.head
        nodes = []
        while node is not None:
            nodes.append(str(node.doc_id))
            node = node.next
        return " ".join(nodes)


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def exec_operation(listA, listB, operation):
    """
    This function takes two postings lists and does a specified OPERATION on those lists.
    Returns the resulting postings list after said operation on the lists.
    """
    resulting_postings = PostingList()

    if operation == 'AND':
        resulting_postings.head = resulting_postings.and_merge(listA.head, listB.head)
        for node in resulting_postings:
            node.skip = None
    elif operation == 'OR':
        resulting_postings.head = resulting_postings.or_merge(listA.head, listB.head)
        resulting_postings.remove_duplicates(resulting_postings.head)
    elif operation == 'ANDNOT':
        resulting_postings.head = resulting_postings.and_not_merge(listA.head, listB.head)
    elif operation == 'NOT':
        # the query "NOT term" is executed as all_docs AND NOT term. Costly operation!
        resulting_postings.head = resulting_postings.and_not_merge(listA.head, listB.head)
    else:
        print(f'Invalid operation: {operation}')

    return resulting_postings


def normalize_token(token):
    """
    Case-folds and porter-stems a token (str word). Returns a normalized token (str word).
    """
    token = token.lower()  # case folding
    token = PORTER_STEMMER.stem(token)  # porter-stemming
    return token


def shunting_yard(q):
    """
    Parses a logical expression q (str) into a postfix notation (list) of terms and operations
    that follow the rules of the logic.
    Inspiration for code: https://en.wikipedia.org/wiki/Shunting-yard_algorithm
    """

    q = q.replace('(', '( ')
    q = q.replace(')', ' )')

    tokens = q.split()

    output_q = []   # queue implementation, use q.append() and q.pop(0) for add/remove
    operator_stack = []  # stack implementation, use stack.append() and stack.pop() for add/remove

    for token in tokens:
        if token in OPERATORS:
            while len(operator_stack) > 0 and operator_stack[-1] != '(' \
                    and (PRECEDENCE_DICT[operator_stack[-1]] > PRECEDENCE_DICT[token] or
                         PRECEDENCE_DICT[operator_stack[-1]] == PRECEDENCE_DICT[token] and token != 'NOT'):
                output_q.append(operator_stack.pop())
            operator_stack.append(token)

        elif token == '(':
            operator_stack.append(token)

        elif token == ')':
            while operator_stack[-1] != '(':
                if len(operator_stack) < 1:
                    raise "MismatchError"
                output_q.append(operator_stack.pop())
            operator_stack.pop()  # pop the left parenthesis from the stack and discard it

        else:  # token must be a search term
            output_q.append(normalize_token(token))

    while len(operator_stack) > 0:
        top_of_stack = operator_stack.pop()
        if top_of_stack == '(' or top_of_stack == ')':
            raise "MismatchError"
        output_q.append(top_of_stack)
    return output_q


def retrieve_postings_list(dictionary, term_id):
    """
    Takes a term id and retrieves its posting list by using the dictionary to find the offset
    in the file the posting list was written to. Returns said postings list.
    """
    with open(postings_file, 'rb') as read_postings:
        reader_offset = dictionary[term_id][1]
        read_postings.seek(reader_offset)
        return pickle.load(read_postings)


def search_term(term_to_search, dictionary):
    """
    Converts a term (str) to a posting list. Tries to first convert the term (str) to a term id (int) and
    then uses this term id to call a function that retrieves the posting list.
    """
    searched_term = normalize_token(term_to_search) if term_to_search != 'all_documents_combined' else term_to_search
    try:
        term_id = term_to_term_id[searched_term]
    except KeyError:
        return PostingList()    # if a query term does not exist, just return an empty posting list

    return retrieve_postings_list(dictionary, term_id)


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform search on the given queries file and output the search results to a file
    """
    print('Running search on the queries ...')

    with open(dict_file, 'rb') as read_dict:
        # We are able to read the full dictionary into memory
        # The dictionary is structured as - term_id : (doc_freq, file_offset)
        dictionary = pickle.load(read_dict)

    # create / wipe the results file before we start handling the queries
    open(results_file, 'w').close()

    with open(queries_file, 'r') as queries:
        for query in queries:
            RPN = shunting_yard(query)  # Process this query

            # print(f'Searching for query: {query} which is translated to RPN: {RPN}')

            result = None  # we will iteratively write our results to this variable and it will
            # be the postings list we return in the end.
            i = 0
            while i < len(RPN):
                token = RPN[i]

                if token in OPERATORS:
                    if token == 'AND':
                        result = exec_operation(last_term, result, 'AND')
                    elif token == 'OR':
                        result = exec_operation(last_term, result, 'OR')
                    elif token == 'NOT':
                        if i + 1 < len(RPN):
                            next_token = RPN[i+1]
                            if next_token in OPERATORS:
                                if next_token == 'AND':
                                    result = exec_operation(result, last_term, 'ANDNOT')
                                elif next_token == 'OR':
                                    # all_docs_list is a posting list that contains ALL document id's in
                                    # sorted order. It is used to handle some (NOT term) queries, where we
                                    # use the all_docs_list and subtract all postings in the posting list of "term".
                                    all_docs_list = search_term('all_documents_combined', dictionary)
                                    not_last_term = exec_operation(all_docs_list, last_term, 'NOT')
                                    result = exec_operation(result, not_last_term, 'OR')
                                elif next_token == 'NOT':  # double negation, so we can just use the value we had before
                                    result = result
                                i += 1  # if we used one of these, we skip an extra step in
                                # this iteration since we used two operations at once
                        else:
                            all_docs_list = search_term('all_documents_combined', dictionary)
                            result = exec_operation(all_docs_list, last_term, 'NOT')
                else:
                    last_term = search_term(token, dictionary)
                    if result is None:
                        # for the very first iteration, we do not have a result set yet,
                        # so we set it manually, and later it will keep on accumulating results
                        # from the queries while being processed.
                        result = last_term
                i += 1

            with open(results_file, 'a') as write_res:
                write_res.write(str(result) + '\n')

        print("... done with evaluating queries")


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
