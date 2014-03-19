Hosts-File-Generator
====================

Generates and merges a hosts file from a list of sources.


```
usage: block-ads.py [-h] [-a ADD] [-r REMOVE] [--gen] [--dir DIR] [--list]

This is a script that creates and merges a hosts file from certain sources.

optional arguments:
  -h, --help            show this help message and exit
  -a ADD, --add ADD     Add a hosts source or sources separated by commas
  -r REMOVE, --remove REMOVE
                        Remove a hosts source or sources separated by commas
  --gen                 Generates the hosts file
  --dir DIR             The directory to store the hosts file in,defaults to
                        current directory and can be a csv list of directories
  --list                Lists the sources in the hosts file
```