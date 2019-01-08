#!/usr/bin/env python3
import requests, time
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import sqlite3
import hashlib
from sqlite3 import Error


# Initialization
db_file = 'database.db'

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None

try:
    conn = create_connection(db_file)
    cur = conn.cursor()
    while True:
        cur.execute("SELECT * FROM watchlist")
        rows = cur.fetchall()
        for row in rows:
            # time.sleep(100)

            # Get each column from each row of data
            username = row[0]
            URL = row[1]
            dbhash = row[2]
            lastchecked = row[3]
            status = row[4]
            statuscode = row[5]
            dateObj = datetime.strptime(lastchecked,"%Y-%m-%d %H:%M:%S")
            
            # Edit time interval here
            timeCheck = dateObj + timedelta(seconds = 30)
            if datetime.now() > timeCheck:

                if status == 'false':
                    isdown = False
                else:
                    isdown = True
                if row[5] != "200":
                    not200 = True
                else:
                    not200 = False
                    
                try:
                    print('Monitoring {} ...'.format(URL))
                    response = requests.get(URL)
                    print(response.status_code)
                    sitehash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()

                    if row[2] != str(sitehash):
                        print('{} site might have changed! Please check URL!{}\n'.format(URL, datetime.now()))

                    if isdown or not200:
                        print('{} returned to normal at {}'.format(URL, datetime.now()))
                        cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime'),sitedown='false',statuscode=? WHERE username=? AND url=?''',(response.status_code,username,URL))

                    if response.status_code != 200:
                        if not200 is False:
                            code = response.status_code
                            print('{} returned status {} at {}'.format(URL, code, datetime.now()))
                            not200 = True
                            cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime'),statuscode=? WHERE username=? AND url=?''',(response.status_code,username,URL))
                        else:
                            cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime') WHERE username=? AND url=?''',(username,URL))
                    else:
                        cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime'),statuscode=? WHERE username=? AND url=?''',(response.status_code,username,URL))
                
                except Exception as e:
                    if isdown is False:
                        print('{} might be down! {}\n Error: {}\n'.format(URL, datetime.now(), str(e)))
                        isdown = True
                        cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime'),sitedown='true' WHERE username=? AND url=?''',(username,URL))
                    else:
                        cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime') WHERE username=? AND url=?''',(username,URL))

                conn.commit()
except KeyboardInterrupt:
    print('\nExiting...')
