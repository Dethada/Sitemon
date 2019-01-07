#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create table
# c.execute('''CREATE TABLE watchlist (
#             username TEXT NOT NULL,
#             url TEXT NOT NULL,
#             hash TEXT NOT NULL,
#             lastchecked TEXT NOT NULL,
#             sitedown TEXT NOT NULL,
#             statuscode TEXT NOT NULL,
#             PRIMARY KEY (username, url)
#             )''')

# Insert a row of data
c.execute('''INSERT INTO watchlist VALUES (
    'testuser',
    'https://yahoo.com',
    'b1e65bfbc2e1bf984e7c6786bd1ebed933fb8567',
    DATETIME('now','localtime'),
    'false',
    '200'
    )''')

# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()