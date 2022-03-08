# Homework #2 » Boolean Retrieval

### Python version
`Python Version 3.7.6`

## Commands:

### Run indexing
```
    python3 index.py -i nltk_data/corpora/reuters/training/ -d dictionary.txt -p postings.txt
```

### Run searching
```
    python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o search_results.txt
```

## Submission description
The `index.py` reads in the reuters corpus and has the goal of creating a dictionary and one postings list for every term that occurred in the corpus. In addition, the program should be memory efficient and have some memory constraints. Hence, we used the technique of BSBI, and divided all documents into 10 separate blocks. These were processed separately and written to disc using `pickle.dump()` before continuing with the next block. 

Once all documents in the corpus has been processed, the blocks are again retrieved from disc, binary merged and then written back to disc to later be accessed when searching in `search.py`. 

In order to facilitate the storing of the document ids, we have implemented a linked list data structure. This allowed us to store the document ids for each term, and also gave a very intuitive understanding of skip pointers. This proved useful for the boolean queries, but it also led to some difficulties due to the complexity of working with this data structure. 

To query expressions, we make use of three files: One for converting terms to term_ids and vice versa, one for a dictionary that keeps track of all terms in the corpus, and at what byte their posting list is written, and also the file that contains all the posting lists. By combining this files, we can get read points from the dictionary that corresponds exactly to the posting list that we want to retrieve. 

Subsequently, we read the query and use a shunting yard algorithm to process the queries in a specific order. After that, we carried out the respective boolean operations. It involved merging the linked list in the below mentioned ways:
 
| Operation     | Description |
| -----------   | ----------- |
| a AND b       |  	Merge the linked lists to find intersection of a and b. |
| a OR b        | 	Merge the linked lists to get all the terms. The union between a and b, with duplicate postings removed. |
| NOT b         | 	Merge linked list of term b with the linked list that contains all the document ids to obtain the ids which do not store b. |
| a AND NOT b   | 	Merge two linked list with the intuition that result = postingList(a) - postingList(b) |
| a OR NOT b    |	First find "NOT b" in the above mentioned way, the do "a OR (NOT b)" |

## Files
| File Name             | Description of file |
| -----------           | ----------- |
| index.py	            | takes several documents, indexes all words and writes dictionaries and posting lists to two files |      
| search.py	            | takes a file of search queries and uses the dictionary and postings to answer them |
| dictionary.txt        | holds the dictionary term_id : (doc.freq, file_offset) |
| postings.txt	        | holds one pickled posting list (linked list) for each term |
| term_conversion.txt   | holds two pickled dictionaries, term : term_id and term_id : term |

## References 

* [Shunting Yard algorithm](https://en.wikipedia.org/wiki/Shunting-yard_algorithm)
* [Algorithm for merging two linked lists](https://www.geeksforgeeks.org/merge-two-sorted-linked-list-without-duplicates/)