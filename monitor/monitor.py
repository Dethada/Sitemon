#!/usr/bin/env python3
import requests, time
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import sqlite3
import hashlib
from sqlite3 import Error
import logging
from settings import *

logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=LOG_FILE,
                    filemode='a')

class Site():
    def __init__(self, username, url, sitehash, lastchecked, sitedown, statuscode):
        self.username = username
        self.url = url
        self.sitehash = sitehash
        self.lastchecked = datetime.strptime(lastchecked,"%Y-%m-%d %H:%M:%S")
        self.sitedown = sitedown
        self.statuscode = statuscode

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None

def update_lastchecked(cur, site):
    cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime') WHERE username=? AND url=?''',(site.username,site.url))

def update_sitedown(cur, site, status):
    cur.execute('''UPDATE watchlist SET sitedown=? WHERE username=? AND url=?''',(status,site.username,site.url))

def update_statuscode(cur, site, statuscode):
    cur.execute('''UPDATE watchlist SET statuscode=? WHERE username=? AND url=?''',(statuscode,site.username,site.url))

def update_sitehash(cur, site, sitehash):
    cur.execute('''UPDATE watchlist SET hash=? WHERE username=? AND url=?''',(sitehash,site.username,site.url))

def notify_user(site, msg):
    endpoint = 'https://api.telegram.org/bot{}/sendMessage'.format(TELE_TOKEN)
    data = {"chat_id":site.username,"text":msg}
    r = requests.post(endpoint, json=data)
    if r.status_code == 400:
        logging.error('Status: {}\tText: {}'.format(r.status_code, r.text))
    elif r.status_code == 200:
        logging.info('Status: {}\tText: {}'.format(r.status_code, r.text))
    else:
        logging.warn('Status: {}\tText: {}'.format(r.status_code, r.text))

def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM watchlist")
    rows = cur.fetchall()
    for row in rows:
        time.sleep(CHECK_FREQUENCY)

        site = Site(row[0], row[1], row[2], row[3], row[4], row[5])
        
        timeCheck = site.lastchecked + timedelta(seconds=POLL_FREQUENCY)
        if datetime.now() >= timeCheck:
            try:
                logging.info('Monitoring {} ...'.format(site.url))
                update_lastchecked(cur, site)
                response = requests.get(site.url)
                sitehash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()

                if site.sitedown == 'true':
                    notify_user(site, '{} is up again at {}'.format(site.url, current_time()))
                    update_sitedown(cur,site,'false')

                if site.sitehash != sitehash:
                    notify_user(site, '{} might have changed! Please check URL!{}\n'.format(site.url, current_time()))
                    update_sitehash(cur, site, sitehash)

                if str(response.status_code) != site.statuscode:
                    notify_user(site, '{} returned status {} at {}'.format(site.url, response.status_code, current_time()))
                    update_statuscode(cur, site, response.status_code)
            
            # catch all requests exceptions
            except requests.exceptions.RequestException as e:
                if site.sitedown == 'false':
                    notify_user(site, '{} might be down! {}\n Error: {}\n'.format(site.url, current_time(), str(e)))
                    update_sitedown(cur,site,'true')
            conn.commit()

def main():
    conn = create_connection(DB_FILE)
    try:
        while True:
            run(conn)
    except KeyboardInterrupt:
        print('\nExiting...')
        conn.close()

if __name__ == '__main__':
    main()
