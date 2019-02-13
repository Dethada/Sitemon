#!/usr/bin/env python3
"""
Monitors for changes for each site in the database and notifies the users.
"""

import time
from datetime import datetime
from datetime import timedelta
import sqlite3
from sqlite3 import Error
import logging
import random
import os
import uuid
from collections import namedtuple
import requests
from PIL import Image
import imagehash
from settings import *

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


Site = namedtuple('Site', [
    'username',
    'url',
    'sitehash',
    'lastchecked',
    'sitedown',
    'statuscode'
])


def create_connection(db_file):
    """
    Create a database connection to the SQLite database specified by the file name

    :param fname: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as err:
        print(err)

    return None


def update_lastchecked(cur, site):
    """
    Update the last time the site is checked

    :param cur: database cursor
    :param site: named tuple containing site data
    """
    cur.execute('''UPDATE watchlist SET lastchecked=DATETIME('now','localtime') WHERE username=? AND url=?''',
                (site.username, site.url))


def update_sitedown(cur, site, status):
    """
    Update whether the site is down

    :param cur: database cursor
    :param site: named tuple containing site data
    :param status: string 'true' if site is down or 'false' if site is up
    """
    cur.execute('''UPDATE watchlist SET sitedown=? WHERE username=? AND url=?''',
                (status, site.username, site.url))


def update_statuscode(cur, site, statuscode):
    """
    Update the http response code of the site

    :param cur: database cursor
    :param site: named tuple containing site data
    :param statuscode: the http response code of the site (int)
    """
    cur.execute('''UPDATE watchlist SET statuscode=? WHERE username=? AND url=?''',
                (statuscode, site.username, site.url))


def update_sitehash(cur, site, sitehash):
    """
    Update the perceptual hash of the site

    :param cur: database cursor
    :param site: named tuple containing site data
    :param sitehash: the perceptual hash of the site
    """
    cur.execute('''UPDATE watchlist SET hash=? WHERE username=? AND url=?''',
                (sitehash, site.username, site.url))


def notify_user(site, msg):
    """
    Send a message to the user

    :param site: named tuple containing site data
    :param msg: message to send to the user
    """
    endpoint = 'https://api.telegram.org/bot{}/sendMessage'.format(TELE_TOKEN)
    data = {"chat_id": site.username, "text": msg}
    response = requests.post(endpoint, json=data)
    if response.status_code == 400:
        logging.error('Status: {}\tText: {}'.format(
            response.status_code, response.text))
    elif response.status_code == 200:
        logging.info('Status: {}\tText: {}'.format(
            response.status_code, response.text))
    else:
        logging.warning('Status: {}\tText: {}'.format(
            response.status_code, response.text))


def current_time():
    """
    Get the current time

    :return: The current time
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def getsitehash(url):
    """
    Gets the perceptual hash of a site

    :param url: the url of the site
    :return: The perceptual hash of the fullpage screen shot of the site or None if it failed
    """
    tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
    os.system('utils/screenshot.js -u \'{}\' -o {}'.format(url, tempname))
    try:
        sitehash = str(imagehash.phash(Image.open(tempname)))
    except FileNotFoundError:
        return None
    if os.path.isfile(tempname):
        os.remove(tempname)
    return sitehash


def check(filename):
    """
    Goes through the database and does all the status checks on the sites

    :param filename: database filename
    """
    conn = create_connection(filename)
    cur = conn.cursor()
    cur.execute("SELECT * FROM watchlist")
    rows = cur.fetchall()
    for row in rows:
        site = Site(row[0], row[1], row[2], datetime.strptime(
            row[3], "%Y-%m-%d %H:%M:%S"), row[4], row[5])

        time_check = site.lastchecked + timedelta(seconds=POLL_FREQUENCY)
        if datetime.now() >= time_check:
            try:
                logging.info('Monitoring {} ...'.format(site.url))
                update_lastchecked(cur, site)
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                response = requests.get(site.url, headers=headers)
                sitehash = getsitehash(site.url)

                if site.sitedown == 'true':
                    notify_user(site, '{} is up again at {}'.format(
                        site.url, current_time()))
                    update_sitedown(cur, site, 'false')

                if site.sitehash != sitehash and sitehash is not None:
                    notify_user(site, '{} might have changed! Please check URL!{}\n'.format(
                        site.url, current_time()))
                    update_sitehash(cur, site, sitehash)

                if str(response.status_code) != site.statuscode:
                    notify_user(site, '{} returned status {} at {}'.format(
                        site.url, response.status_code, current_time()))
                    update_statuscode(cur, site, response.status_code)

            # catch all requests exceptions
            except requests.exceptions.RequestException as err:
                if site.sitedown == 'false':
                    notify_user(site, '{} might be down! {}\n Error: {}\n'.format(
                        site.url, current_time(), str(err)))
                    update_sitedown(cur, site, 'true')
            conn.commit()
    conn.close()


def main():
    """
    main function that runs the check function at set interval
    until keyboard interrupt is recieved
    """
    try:
        while True:
            check(DB_FILE)
            time.sleep(CHECK_FREQUENCY)
    except KeyboardInterrupt:
        print('\nExiting...')
        


if __name__ == '__main__':
    main()
