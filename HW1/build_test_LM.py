#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math
import re
import nltk
import sys
import getopt


def create_ngram(sentence, n):
    return [sentence[i:i + n] for i in range(len(sentence) - n + 1)]


def build_LM(in_file):
    """
    build language models for each label
    each line in in_file contains a label and a string separated by a space
    """
    print("building language models...")

    language_string_to_language_idx = {'malaysian': 0, 'indonesian': 1, 'tamil': 2}

    training_data = []

    with open(in_file, 'r') as input_text:
        for line in input_text:
            split_line = line.split()
            language, text = split_line[0], ' '.join(split_line[1:])  # Separate language and the rest of the
            # string into two variables
            training_data.append([language, text])

    LM = [{}, {}, {}]  # Array that contains three dictionaries, one for each language.

    for lang_dict in LM:
        lang_dict['counter'] = 0  # Introduce a counter for how many ngrams have been used for this specific language.

    for training_row in training_data:
        current_language = language_string_to_language_idx[training_row[0]]
        # Use dictionary to convert language in string representation to a index.

        sentence = training_row[1].lower()
        sentence = re.sub('[^a-zA-Z]+', '', sentence)

        four_gram = create_ngram(sentence, 4)
        # Converts something like 'hello hi' into ['hell', 'ello', 'llo ', 'lo h', 'o hi']

        for gram in four_gram:
            if gram not in LM[0]:  # Check if this gram is NOT in the malaysian dictionary.
                # If the gram have been seen before, it must be in all languages dictionaries (incl. Malaysian)
                for lang_dict in LM:    # If first time we see this gram, we create a new key-value pair
                    # with key = gram and value = 0 in all the three different language dictionaries.
                    lang_dict[gram] = 0

            LM[current_language][gram] += 1  # Add one to the counter of this specific gram for the current language.
            LM[current_language]['counter'] += 1    # The current language have been trained on one more gram,
            # so the counter should be incremented.

    for lang_dict in LM:
        for key in lang_dict.keys():
            if key != 'counter':
                lang_dict[key] += 1  # Add-1 smoothing
                lang_dict['counter'] += 1  # Must also add 1 to the counter for the probabilities to remain
                # stochastic rows.

        for key in lang_dict.keys():
            if key != 'counter':
                # Create probabilities instead of just counting number of appearances.
                lang_dict[key] = math.log(lang_dict[key] / lang_dict['counter'])
                # Log-probabilities to overcome underflow problems.

    return LM


def test_LM(in_file, out_file, LM):
    """
    test the language models on new strings
    each line of in_file contains a string
    you should print the most probable label for each string into out_file
    """
    print("testing language models...")

    language_idx_to_language_string = {0: 'malaysian', 1: 'indonesian', 2: 'tamil'}

    out_text = ''   # This is the string that will be iteratively appended and finally written to the outfile.

    test_data = []

    with open(in_file, 'r') as input_text:
        for line in input_text:
            test_data.append(line)

    for test_line in test_data:
        four_gram = create_ngram(test_line, 4)

        probabilities = [1, 1, 1]  # Initial probability is 1 for all languages.
        gram_c = 0
        new_grams = 0
        for gram in four_gram:

            #gram = gram.lower()
            #gram = re.sub('[^a-zA-Z]+', ' ', gram)

            if gram in LM[0]:  # Check if this gram is in the malaysian dictionary.
                # If the gram have been seen before, it must be in all languages dictionaries (incl. Malaysian)

                for i in range(3):
                    probabilities[i] = probabilities[i] + LM[i][gram]
                    # Multiplication in base_10 space is same as addition in Log space.
                    # Src: https://web.stanford.edu/~jurafsky/slp3/3.pdf (Eq. 3.13)
            else:
                new_grams += 1
            gram_c += 1

        max_prob = max(probabilities)
        most_likely_language_idx = probabilities.index(max_prob)
        # Find the index of the language we find most likely to match the string we test.

        if new_grams / gram_c > 0.9:  # If more than 90% of the input gram haven't been in the training set.
            # Most likely, this is because it is an 'other' language than Malaysian / Indonesian / Tamil.
            most_likely_language_string = 'other'
        else:
            most_likely_language_string = language_idx_to_language_string[most_likely_language_idx]
            # Use a dictionary to convert index to language in string form.

        out_text += f'{most_likely_language_string} {test_line}'    # Append the predicted language and the string we
        # test on to the string that is going to be written to the outfile.

    with open(out_file, 'w') as text_file:
        text_file.write(out_text)   # Write the out string we have iteratively created to the out file.


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -b input-file-for-building-LM -t input-file-for-testing-LM -o output-file"
    )


input_file_b = input_file_t = output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], "b:t:o:")
except getopt.GetoptError:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == "-b":
        input_file_b = a
    elif o == "-t":
        input_file_t = a
    elif o == "-o":
        output_file = a
    else:
        assert False, "unhandled option"
if input_file_b == None or input_file_t == None or output_file == None:
    usage()
    sys.exit(2)

LM = build_LM(input_file_b)
test_LM(input_file_t, output_file, LM)
