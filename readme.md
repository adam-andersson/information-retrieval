# First Setup
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


# Launch
```
ssh e0923089@sunfire.comp.nus.edu.sg    // ssh to sunfire
ssh xcna0.comp.nus.edu.sg               // ssh from sunfire to xcna0 node
```

