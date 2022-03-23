# Homework #1 » Language Detection

### Python version
`Python Version 3.7.6`

Also tested on `Python Version 3.8.10`

## Commands:

### Run indexing
```
    python3 build_test_LM.py -b input.train.txt -t input.test.txt -o input.predict.txt
```

### Run searching
```
    python3 eval.py input.predict.txt input.correct.txt
```

## Score
`101/100` points (`+1` for extra good documentation)

## Submission description
The program trains a language model based on training data from a secondary file. After constructing the language model, the program may test the LM with sentences from a tertiary file to accurately predict if a text is in Indonesian, Malaysian or (phonetically transcribed into English) Tamil.

### Building the Language Model
* Given an input row on the form "correct_language Full_sentence", the program creates all the n-grams of length 4 for the full sentence. This is done in the function create_ngram(). In the function, I've used a window sliding technique to iteratively take the characters between index i and i+4 for all i such that we start with left side of window at i = 0,and end when right side of window at i = idx of last character.
* The program converts all uppercase letters to lowercase for more matching in the testing phase.
* For every ngram, I add the ngram to the dictionary of all languages' models and increment that ngram's counter only
for the correct language.
* After going through all ngrams, I do add-1 smoothing to avoid future multiplication with 0.
* Finally, the probability of every ngram, for all 3 languages is calculated in logarithmic space. This is to avoid
arithmetic underflow. This probability is calculated as the logarithm of the specific ngram's number of appearances
divided by the total number of appearances (incl. those due to the smoothing) for all ngrams for that language.

### Testing the Language Model
* When testing the LM, the program creates n-gram in the exact same way as when building the LM.
* Again, all uppercase letters are converted to lowercase.
* The probability of a sentence belonging to a specific language is calculated by multiplying the probabilities in the
language model. For every ngram that is in the sentence that's going to be predicted: I calculate the probability of
that n-gram being observed by all three language models. This is done by iteratively multiplying the probabilities
(which in logarithmic space is done with addition between the log-probabilities).
* If the ngram is not in the language models, it is skipped and does not affect the probability.
* In case that the sentence is very new to the language models, i.e. if more than 75% of ngrams have not been seen
during training, then I output "other" as my guess of language.
* Else, I output the language that is most likely, i.e. that have the highest probability of observing the given
sentence.

### Experimentation
There was some experimentation to find the sweet spot that gives the most accurate model (based on how it scores on the
test data). Mainly, I experimented with preprocessing of strings such that the n-grams created are most likely to result
in matches during testing. In total, there were three techniques that I experimented with and evaluated:
* Case insensitivity. The only technique I elected to stick with in my implementation. This made the language model find
more matches during the testing, which is good as we want to trust our training set and value our observations more
highly.
* Regex to only allow letters. This had the effect of making less n-grams get matched in the language model, which was
not desirable and hence, not used.
* Start/End tokens. Additionally, I experimented with adding start and end tokens for the sentences as well. However,
this seemed to have a very minor effect on the predictions. This will lead to fewer n-grams getting matched in the
language model, which is not desirable, especially in this case when our training set is quite small.
These experiments were mainly evaluated by the percentage: new_grams / gram_c. If this percentage is higher, it means
that a greater fraction of the test n-grams had not been seen during training. I mainly focused on getting this
percentage low as this means that more of the observations are actually getting used and impacts the predictions.


## Files
| File Name             | Description of file |
| -----------           | ----------- |
| `build_test_LM.py`	            | this program holds the functions for both training a LM and testing that LM |
