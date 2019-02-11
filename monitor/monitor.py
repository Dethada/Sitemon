#!/usr/bin/env python3
import requests
import time
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import sqlite3
import hashlib
from sqlite3 import Error
import logging
from settings import *
import re
import random
import subprocess
from PIL import Image
import imagehash
import os
import uuid

logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=LOG_FILE,
                    filemode='a')

USER_AGENTS = ['Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) brave/0.7.10 Chrome/47.0.2526.110 Brave/0.36.5 Safari/537.36'
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.36 Safari/525.19',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML,like Gecko) Chrome/9.1.0.0 Safari/540.0',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Ubuntu/10.10 Chromium/8.0.552.237 Chrome/8.0.552.237 Safari/534.10']

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

def stripwhitespace(text):
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', text)

def getsitehash(site):
    tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
    process = subprocess.Popen(['utils/screenshot.js', '-u', site.url, '-o', tempname], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    if err:
        logging.error(err)
        return
    sitehash = str(imagehash.phash(Image.open(tempname)))
    if os.path.isfile(tempname):
        os.remove(tempname)
    return sitehash

def check(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM watchlist")
    rows = cur.fetchall()
    for row in rows:
        site = Site(row[0], row[1], row[2], row[3], row[4], row[5])
        
        timeCheck = site.lastchecked + timedelta(seconds=POLL_FREQUENCY)
        if datetime.now() >= timeCheck:
            try:
                logging.info('Monitoring {} ...'.format(site.url))
                update_lastchecked(cur, site)
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(site.url, headers=headers)
                sitehash = getsitehash(response)

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
            check(conn)
            time.sleep(CHECK_FREQUENCY)
    except KeyboardInterrupt:
        print('\nExiting...')
        conn.close()

if __name__ == '__main__':
    main()
