This is the README file for A0247948J's submission
Email(s): E0923089@u.nus.edu

== Python Version ==

I'm using Python Version 3.7.6 for this assignment.

== General Notes about this assignment ==

- Overview of program - 
The program indexes all files of the Reuters training corpus and implements
a ranked retrival model. The program takes free text queries from a file, 
and returns the top 10 search results (or less) for each query to an output 
file. The ranked retrival is based on a Vector Space Model where documents
are ranked according to cosine similarity in a lnc.ltc ranking scheme.

- Indexing of documents `index.py` -
During indexing, the program iterates over all documents. Every word in each
document is case-folded and stemmed. Dictionary and postings lists are 
updated when iterating through all documents. Additionally, each tokens' 
term frequencies in a specific document is used to calculate the weighted 
length of each document.

There are two main dictionaries used during indexing:
`dictionary` keeps track of the tokens' (word) document frequencies.
`postings_list` keeps track of the tokens' (word) term frequencies and the 
document id of all documents where this token is present.
In addition, there are dictionaries for converting between term and term_id
and for tracking document lengths during indexing for use during search.

- Ranked retrieval of documents (`search.py`) -
* For each search query in the query-file, the query is split to its component
words that are consequently case-folded and Porter-stemmed.
* For each term in a query, the TFxIDF value is calculated by the formula: 
(1 + log(termFrequencyInQuery)) * log(numberOfDocuments / documentFrequency)
* For each posting in the term's posting list, the term frequency is 
calculated with the formula: (1 + log(termFrequencyInPosting)) 
* This term frequency is subsequently multiplied with the query term's weight,
and added to a dictionary keeping track of the score for all documents with
terms present in the query.
* The cosine normalization is done by multiplying the above score with the 
inverse square of all query weights summed, and multiplying this with the 
inverse square of the vector length of the document (this is calculated 
during indexing).
* All scores are tracked in a max-heap and the program returns the top 10 
documents (if this many exist) of the heap according to their score.

- Experimentation -
* One point of experimentation was with the data structure for keeping
track of the best search results. I decided on using a max heap of dynamic 
size, which has the risk of growing in size indefinitely, but with regards 
to speed (which is usually what we're conserned with during search) this
option performed the best and hence was used.
* Another point of experimentation was with the preprocessing of terms.
I started off using only case-folding and Porter-stemming, and got the same
results as some others on the forum, but decided to experiment with
processing punctuations for the sake of getting similar results as some
others in the forum. In the end, I decided to stick only with case-folding
and the stemming.

== Files included with this submission ==

* `index.py` takes several documents, indexes all words and writes 
dictionary and posting lists to files
* `search.py` takes a document of queries and retrieves the top search 
results according to a lnc.ltc ranking scheme.
* `dictionary.txt` contains the pickled postings lists 
* `postings.txt` contains the pickled dictionary as well as pointers
to all postings list 
* `term_conversion.txt` contains pickled dictionaries to convert to and 
from term strings and termid integers.
* `document_lengths.txt` contains the number of documents training on and 
the squared vector length of every document
* `README.txt` this file that you're reading right now

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] I/We, A0247948J, certify that I/we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==
