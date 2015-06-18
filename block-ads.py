#!/usr/bin/env python

# The MIT License (MIT)
# Copyright (c) 2014 Forgotten Leaf
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.

__author__ = "Forgotten Leaf"
__copyright__ = "Copyright 2015, Forgotten Leaf"
__license__ = "MIT"
__version__ = "1.0.0"


#==============================================================================
# Imports
#==============================================================================
from os.path import expanduser
from os.path import join
import argparse
import datetime
import os.path
import re
import requests
import sqlite3

#==============================================================================
# Global Variables
#==============================================================================
DB_NAME = '.hosts_sources_db.sqlite'
DB_TABLE_SOURCES = 'Sources'
DB_TABLE_SOURCES_COLUMN_ID = 'id'
DB_TABLE_SOURCES_COLUMN_URL = 'url'
HOME = expanduser("~")

DEFAULT_SOURCES =\
(
    "http://your-source1.com/hosts.txt",
    "http://your-source2.com/hosts.txt"
)

#==============================================================================
# Functions
#==============================================================================

# Taken from:
# https://gist.github.com/gromgull/3922244
# due to a bug with re.sub where it returns None on unmatched groups


def re_sub(pattern, replacement, string):
    def _r(m):
        # Now this is ugly.
        # Python has a "feature" where unmatched groups return None
        # then re.sub chokes on this.
        # see http://bugs.python.org/issue1519638
        
        # this works around and hooks into the internal of the re module...
 
        # the match object is replaced with a wrapper that
        # returns "" instead of None for unmatched groups
 
        class _m():
            def __init__(self, m):
                self.m=m
                self.string=m.string
            def group(self, n):
                return m.group(n) or ""
 
        return re._expand(pattern, _m(m), replacement)
    
    return re.sub(pattern, _r, string)


def add_source(sourceName):
    conn = sqlite3.connect(join(HOME, DB_NAME))

    query =\
    'INSERT INTO "{}" ("{}") VALUES ("{}")'\
    .format(DB_TABLE_SOURCES,
            DB_TABLE_SOURCES_COLUMN_URL,
            sourceName)

    conn.execute(query)
    print("Added source:", sourceName)

    conn.commit()
    conn.close()


def remove_source(sourceName):
    conn = sqlite3.connect(join(HOME, DB_NAME))

    query = \
    'DELETE FROM "{}" WHERE "{}" = "{}"'\
    .format(DB_TABLE_SOURCES,
            DB_TABLE_SOURCES_COLUMN_URL,
            sourceName)

    conn.execute(query)
    print("Removed source:", sourceName)

    conn.commit()
    conn.close()


def source_exists(sourceName):
    conn = sqlite3.connect(join(HOME, DB_NAME))

    query = 'SELECT * FROM "{}" WHERE "{}" = "{}"'\
    .format(DB_TABLE_SOURCES, DB_TABLE_SOURCES_COLUMN_URL, sourceName)

    cursor = conn.execute(query)
    exists = cursor.fetchone()

    conn.close()
    return exists is not None


def setup_db_if_not_exists():
    dbFile = join(HOME, DB_NAME)
    if not os.path.exists(dbFile):
        setup_db()


def setup_db():
    conn = sqlite3.connect(join(HOME, DB_NAME))
    query =\
    'CREATE TABLE "{}"'\
    '("{}" INTEGER PRIMARY KEY AUTOINCREMENT,"{}" TEXT NOT NULL)'\
    .format(DB_TABLE_SOURCES,
            DB_TABLE_SOURCES_COLUMN_ID,
            DB_TABLE_SOURCES_COLUMN_URL)

    conn.execute(query)
    conn.close()

    for source in DEFAULT_SOURCES:
        add_source(source)


def get_sources():
    conn = sqlite3.connect(join(HOME, DB_NAME))
    query = 'SELECT "{}" FROM "{}"'\
    .format(DB_TABLE_SOURCES_COLUMN_URL, DB_TABLE_SOURCES)

    cursor = conn.execute(query)
    sources = list()

    for row in cursor:
        sources.append(row[0])

    conn.close()
    return sources


def list_sources():
    print("\nSources:")

    for row in get_sources():
        print('\t', row)

    print("")


def generate_file(dirPaths):
    sources = get_sources()
    downloadedFileContents = list()
    uniqueSet = set()
    formattedDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    newFileContents = "# Updated on " + formattedDate + "\n"\
    "# This file is generated from the following sources:\n"

    for source in sources:
        line = "# {}\n".format(source)
        newFileContents += line
        response = requests.get(source)

        if response.status_code == 200:
            content = str(response.text)

            # Some websites use 127.0.0.1 instead of 0.0.0.0
            # which is faster to lookup, replace it
            content = content.replace("127.0.0.1", "0.0.0.0")

            # Replace weird whitespace after ip addresses with one space
            content = re_sub("(0.0.0.0)\\s{2,}|\\t{1,}", "\\1 ", content)

            # Find lines that end with a # and make them start on their own
            # lines
            content = re_sub("(.*)(#.*)", "\\1\n\\2", content)

            downloadedFileContents.append(content)

        else:
            print("Unable to reach: ", source)

    newFileContents += "\n127.0.0.1 localhost\n::1 localhost\n\n"

    for fileContents in downloadedFileContents:
        fileContentsSplitByLine = fileContents.splitlines()
        for line in fileContentsSplitByLine:
            if (len(line) != 0):
                if (line[0] != "#"):
                    lineStr = "{}\n".format(line)
                    uniqueSet.add(lineStr)

    for uniqueSource in uniqueSet:
        line = "{}".format(uniqueSource)
        newFileContents += line

    for dirPath in dirPaths:
        file = open(os.path.join(dirPath, 'hosts'), 'w')
        file.write(newFileContents)
        file.close()

#==============================================================================
# Main
#==============================================================================

setup_db_if_not_exists()

parser = argparse.ArgumentParser(description='This is a script '
                                 'that creates and merges a hosts file'
                                 ' from certain sources.'
                                 )

parser.add_argument('-a', '--add', help='Add a hosts source or sources separated by commas', type=str,
                    required=False)

parser.add_argument('-r', '--remove',
                    help='Remove a hosts source or sources separated by commas', type=str, required=False)

parser.add_argument('--gen',
                    help='Generates the hosts file',
                    required=False,
                    action="store_true")

parser.add_argument('--dir',
                    help='The directory to store the hosts file in,'
                    'defaults to current directory and can be a csv list of '
                    'directories',
                    required=False)

parser.add_argument('--list',
                    help='Lists the sources in the hosts file', required=False,
                    action="store_true")

args = parser.parse_args()
if args.add:
    sources = args.add.split(",")

    for source in sources:
        if source_exists(source):
            print("Source:", source,"already exists!")

        else:
            result = add_source(source)

elif args.remove:
    sources = args.remove.split(",")

    for source in sources:
        if not source_exists(source):
            print("Source:", source,"does not exists")

        else:
            result = remove_source(source)

elif args.gen:
        if args.dir:
            dirs = args.dir.split(",")
            generate_file(dirs)

        else:
            generate_file('./')

elif args.list:
    list_sources()
