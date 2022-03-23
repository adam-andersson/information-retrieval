# Information Retrieval
This repository contains homework assignments from the course CS3245 Information Retrieval, taken at National University of Singapore 2022.

## Summary of homeworks
### HW1
This program trains a language model based on training data from a secondary file. After constructing the language model, the LM is used with sentences from a tertiary file to accurately predict if a text is in Indonesian, Malaysian or (phonetically transcribed into English) Tamil.

### HW2
The program creates a boolean index from the Reuters training corpus. This is created using BSBI techniques of dividing into 10 blocks, and postings list contains skip pointers for faster merging. The index can be queried with boolean queries, these queries are parsed using the Shunting Yard algorithm and then use different merge operations to merge posting lists into a final search result list for the query.

### HW3
The program indexes all files of the Reuters training corpus and implements a ranked retrival model. The program takes free text queries from a file, and returns the top 10 search results (or less) for each query to an output file. The ranked retrival is based on a Vector Space Model where documents are ranked according to cosine similarity in a [lnc.ltc](https://nlp.stanford.edu/IR-book/html/htmledition/document-and-query-weighting-schemes-1.html) ranking scheme.

## ssh to testing node
### First Setup
From host terminal: SSH to intermediate server (sunfire) at SoC Network.
```
ssh e0923089@sunfire.comp.nus.edu.sg
```

From host terminal: scp files to sunfire@ssh.
```
scp -r nltk-3.6.7 e0923089@sunfire.comp.nus.edu.sg:
```

From sunfire@ssh: scp files to xcna0 node.
```
scp -r nltk-3.6.7 xcna0:
```

From sunfire@ssh: ssh to cluster node (xcna0).
```
ssh xcna0.comp.nus.edu.sg
```

At xcna0 node: Install NLTK.
```
python3 setup.py install --user
```


### Launch
```
ssh e0923089@sunfire.comp.nus.edu.sg    // ssh to sunfire
ssh xcna0.comp.nus.edu.sg               // ssh from sunfire to xcna0 node
```

