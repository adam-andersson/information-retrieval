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


def build_LM(in_file):
    """
    build language models for each label
    each line in in_file contains a label and a string separated by a space
    """
    print("building language models...")

    input_list = []

    with open(in_file, 'r') as input_text:
        for line in input_text:
            split_line = line.split()
            input_list.append([split_line[0], split_line[1:]])

    cleaned_list = []
    for entry in input_list:
        clean_string = ' '.join(entry[1])
        cleaned_list.append([entry[0], clean_string])

    malay_dict = {'malay_counter': 0}
    indonesian_dict = {'indonesian_counter': 0}
    tamil_dict = {'tamil_counter': 0}

    for training_data in cleaned_list:

        current_language = training_data[0]
        sentence = training_data[1]
        n = 4

        four_gram = [sentence[i:i + n] for i in range(len(sentence) - n + 1)]

        for gram in four_gram:  # TODO: Init empty dicts if no match. Then increment only for matching curr language.
            if gram in malay_dict:  # if it is in either language's dict, it must be in this one too
                if current_language == 'malaysian':
                    malay_dict[gram] += 1
                    malay_dict['malay_counter'] += 1
                if current_language == 'indonesian':
                    indonesian_dict[gram] += 1
                    indonesian_dict['indonesian_counter'] += 1
                if current_language == 'tamil':
                    tamil_dict[gram] += 1
                    tamil_dict['tamil_counter'] += 1
            else:
                if current_language == 'malaysian':
                    malay_dict[gram] = 1
                    malay_dict['malay_counter'] += 1
                    indonesian_dict[gram] = 0
                    tamil_dict[gram] = 0

                if current_language == 'indonesian':
                    indonesian_dict[gram] = 1
                    indonesian_dict['indonesian_counter'] += 1
                    malay_dict[gram] = 0
                    tamil_dict[gram] = 0

                if current_language == 'tamil':
                    tamil_dict[gram] = 1
                    tamil_dict['tamil_counter'] += 1
                    malay_dict[gram] = 0
                    indonesian_dict[gram] = 0

    print(malay_dict['malay_counter'])
    print(indonesian_dict['indonesian_counter'])
    print(tamil_dict['tamil_counter'])

    for key in malay_dict.keys():
        if key != 'malay_counter':
            malay_dict[key] += 1  # Add-1 smoothing
            malay_dict['malay_counter'] += 1

    for key in indonesian_dict.keys():
        if key != 'indonesian_counter':
            indonesian_dict[key] += 1  # Add-1 smoothing
            indonesian_dict['indonesian_counter'] += 1

    for key in tamil_dict.keys():
        if key != 'tamil_counter':
            tamil_dict[key] += 1  # Add-1 smoothing
            tamil_dict['tamil_counter'] += 1

    print(malay_dict['malay_counter'])
    print(indonesian_dict['indonesian_counter'])
    print(tamil_dict['tamil_counter'])

    c_malay = malay_dict['malay_counter']
    for key in malay_dict.keys():
        if key != 'malay_counter':
            malay_dict[key] = math.log(malay_dict[key] / c_malay)   # log-probabilities to overcome underflow problems.

    c_indonesian = indonesian_dict['indonesian_counter']
    for key in indonesian_dict.keys():
        if key != 'indonesian_counter':
            indonesian_dict[key] = math.log(indonesian_dict[key] / c_indonesian)

    c_tamil = tamil_dict['tamil_counter']
    for key in tamil_dict.keys():
        if key != 'tamil_counter':
            tamil_dict[key] = math.log(tamil_dict[key] / c_tamil)

    return [malay_dict, indonesian_dict, tamil_dict]


def test_LM(in_file, out_file, LM):
    """
    test the language models on new strings
    each line of in_file contains a string
    you should print the most probable label for each string into out_file
    """
    print("testing language models...")

    malay_dict, indonesian_dict, tamil_dict = LM

    input_list = []

    with open(in_file, 'r') as input_text:
        for line in input_text:
            input_list.append(line)

    out_text = ''

    for test_line in input_list:
        n = 4
        four_gram = [test_line[i:i + n] for i in range(len(test_line) - n + 1)]

        # eval malay
        malay_prob = 1
        indonesian_prob = 1
        tamil_prob = 1

        for gram in four_gram:
            if gram in malay_dict:
                malay_prob = malay_prob + malay_dict[gram]  # Multiplication in base_10 space is same as addition in
                # Log space. Src: https://web.stanford.edu/~jurafsky/slp3/3.pdf (Eq. 3.13)
                indonesian_prob = indonesian_prob + indonesian_dict[gram]
                tamil_prob = tamil_prob + tamil_dict[gram]

        max_prob = max(malay_prob, indonesian_prob, tamil_prob)

        if max_prob == 1:  # This means that none of the input gram have ever been trained on before.
            # Must be due to 'other' language.
            max_likely_lang = 'other'
        elif malay_prob == max_prob:
            max_likely_lang = 'malaysian'
        elif indonesian_prob == max_prob:
            max_likely_lang = 'indonesian'
        elif tamil_prob == max_prob:
            max_likely_lang = 'tamil'
        else:
            max_likely_lang = 'other'

        # out_text += f'{max_likely_lang} {malay_prob} {indonesian_prob} {tamil_prob} {test_line}'
        out_text += f'{max_likely_lang} {test_line}'

    with open(out_file, "w") as text_file:
        text_file.write(out_text)


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
