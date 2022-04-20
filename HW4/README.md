# Homework #4 » Legal Case Retrieval Mini Project

### Python version
`Python Version 3.7.6`

Also tested on `Python Version 3.8.10`

## Commands:

### Run indexing
```
    python3 index.py -i dataset.csv -d dictionary.txt -p postings.txt
```

### Run searching
```
    python3 search.py -d dictionary.txt -p postings.txt -q queries/queries_example.txt -o search_results.txt
```

### Files to and from the SoC Cluster
ssh from local to sunfire
```
    ssh e0923089@sunfire.comp.nus.edu.sg
```
ssh from sunfire to node (xcna0)
```
    ssh xcna0.comp.nus.edu.sg
```
send file from node to sunfire
```
    scp -r folder_to_send/ e0923089@sunfire.comp.nus.edu.sg:
```

fetch file from sunfire to local machine
```
    scp -r e0923089@sunfire.comp.nus.edu.sg:folder_to_send/ /Users/adamandersson/Desktop/
```
