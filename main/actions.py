"""
Action server for rasa core
"""
import logging
import re
import sqlite3
from sqlite3 import Error
import uuid
import os
import requests
import numpy as np
from PIL import Image
import tensorflow as tf
import imagehash
from rasa_core_sdk import Action

LOG_LEVEL = logging.INFO

# Filename for log file
LOG_FILE = 'actions.log'


# File name for the sqlite3 database
DB_FILE = 'database.db'


logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=LOG_FILE,
                    filemode='a')


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


def process_url(url):
    """
    If the url does not start with http:// or https://, append http:// to it.

    :param url: the url to be processed
    :return: the processed url
    """
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    return url


def get_urls_by_user(username):
    """
    Finds all the urls watched by the user

    :param username: username of the target user
    :return: a list of all the urls watched by the user
    """
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT url FROM watchlist WHERE username=?', (username,))
    urls = cur.fetchall()
    conn.close()
    return urls


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


def insert_url(username, url):
    """
    Insert new url to watch into database, the url
    inserted will be the one after following redirects

    :param username: username of the user that wants to watch the url
    :param url: the url to watch
    :return: True if successful, False if failed
    """
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as err:
        logging.info('Exception: {}'.format(err))
        return False
    if response.status_code != 200:
        logging.info('Status: {}'.format(response.status_code))
        return False
    sitehash = getsitehash(url)
    if sitehash is None:
        return False
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute('''INSERT INTO watchlist VALUES (?,?,?,DATETIME('now','localtime'),'false',?)''',
                (username, response.url, sitehash, response.status_code))
    conn.commit()
    conn.close()
    return True


def remove_url(username, url):
    """
    Remove an url from the database

    :param username: username of the user that wants to remove the url
    :param url: the url to remove
    """
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute('DELETE FROM watchlist WHERE username=? and url=?',
                (username, url))
    conn.commit()
    conn.close()


def clear_watchlist(username):
    """
    Remove all the urls added by the user

    :param username: username of the user that wants to remove all the urls
    """
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute('DELETE FROM watchlist WHERE username=?', (username,))
    conn.commit()
    conn.close()


def geturls(text):
    """
    Finds all the urls in the string

    :param text: the string to search in
    :return: set of urls found in the string
    """
    urlregex = re.compile(
        r'(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?')

    urls = set()
    for word in text.split(' '):
        match = urlregex.search(word)
        if match:
            urls.add(match.group())

    return urls


_MODEL_DIR = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'saved_model')

_IMAGE_SIZE = 64
_BATCH_SIZE = 128

_LABEL_MAP = {0: 'drawings', 1: 'hentai', 2: 'neutral', 3: 'porn', 4: 'sexy'}


def standardize(img):
    mean = np.mean(img)
    std = np.std(img)
    img = (img - mean) / std
    return img


def load_image(infilename):
    img = Image.open(infilename)
    img = img.resize((_IMAGE_SIZE, _IMAGE_SIZE))
    img.load()
    data = np.asarray(img, dtype=np.float32)
    data = standardize(data)
    return data


def predict(image_path):
    with tf.Session() as sess:
        graph = tf.get_default_graph()
        tf.saved_model.loader.load(
            sess, [tf.saved_model.tag_constants.SERVING], _MODEL_DIR)
        inputs = graph.get_tensor_by_name("input_tensor:0")
        probabilities_op = graph.get_tensor_by_name('softmax_tensor:0')
        class_index_op = graph.get_tensor_by_name('ArgMax:0')

        image_data = load_image(image_path)
        probabilities, class_index = sess.run([probabilities_op, class_index_op],
                                              feed_dict={inputs: [image_data] * _BATCH_SIZE})

        probabilities_dict = {_LABEL_MAP.get(
            i): l for i, l in enumerate(probabilities[0])}
        pre_label = _LABEL_MAP.get(class_index[0])
        result = {"class": pre_label, "probability": probabilities_dict}
        return result


class ActionNsfwCheck(Action):
    """ action_nsfw_check class """

    def name(self):
        return "action_nsfw_check"

    def run(self, dispatcher, tracker, domain):
        new_sites = set(tracker.get_latest_entity_values('url'))
        new_sites = new_sites.union(geturls(tracker.latest_message['text']))
        p_sites = list(map(process_url, new_sites))
        msg = ''
        if not p_sites:
            dispatcher.utter_message('You have not entered a valid url')
        else:
            dispatcher.utter_message('Checking whether sites are nsfw')
            for site in p_sites:
                tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
                os.system(
                    'utils/screenshot.js -u \'{}\' -o {}'.format(site, tempname))
                if not os.path.isfile(tempname):
                    msg += 'An error occured when checking {}\n'.format(site)
                    continue
                categorydict = predict(tempname)
                msg += '{} belongs to {} the category\n'.format(
                    site, categorydict.get('class'))
                os.remove(tempname)
            dispatcher.utter_message(msg)
        return []


class ActionMonitorSite(Action):
    """ action_monitor_site class """

    def name(self):
        # type: () -> Text
        return "action_monitor_site"

    def run(self, dispatcher, tracker, domain):
        username = tracker.sender_id
        logging.info('Sender_id: {}'.format(username))
        sites = get_urls_by_user(username)

        new_sites = set(tracker.get_latest_entity_values('url'))

        new_sites = new_sites.union(geturls(tracker.latest_message['text']))
        msg = ''
        if sites:
            for site in new_sites:
                p_site = process_url(site)
                if (p_site,) not in sites:
                    if insert_url(username, p_site):
                        msg += 'Added {} to watch list\n'.format(p_site)
                    else:
                        msg += 'Failed to add {} to watch list\n'.format(
                            p_site)
        else:
            for site in new_sites:
                p_site = process_url(site)
                if insert_url(username, p_site):
                    msg += 'Added {} to watch list\n'.format(p_site)
                else:
                    msg += 'Failed to add {} to watch list\n'.format(p_site)

        # logging.info('Sites: {}'.format(sites))
        if msg == '':
            msg = 'You have not entered an url or an url that is already in your watch list.'
        dispatcher.utter_message(msg)
        return []


class ActionStatus(Action):
    """ action_status class """

    def name(self):
        return "action_status"

    def run(self, dispatcher, tracker, domain):
        username = tracker.sender_id
        sites = get_urls_by_user(username)

        if sites:
            msg = 'Current watch list\n'
            for index, url in enumerate(sites):
                msg += '{}. {}\n'.format(index+1, url[0])

            dispatcher.utter_message(msg)
        else:
            dispatcher.utter_message('Not watching any sites')

        return []


class ActionRemoveSite(Action):
    """ action_remove_site class """

    def name(self):
        return "action_remove_site"

    def run(self, dispatcher, tracker, domain):
        username = tracker.sender_id
        sites = get_urls_by_user(username)
        logging.info('Sites: {}'.format(sites))
        remove_sites = set(tracker.get_latest_entity_values('url'))

        remove_sites = remove_sites.union(
            geturls(tracker.latest_message['text']))
        msg = ''
        if sites:
            for site in remove_sites:
                p_site = process_url(site)
                logging.info('Processed Site: {}'.format(p_site))
                if (p_site,) in sites:
                    remove_url(username, p_site)
                    msg += 'Removed {} from watch list\n'.format(p_site)

        if msg == '':
            msg = 'No sites removed'
        dispatcher.utter_message(msg)

        return []


class ActionRemoveAllSites(Action):
    """ action_remove_all_sites class """

    def name(self):
        return "action_remove_all_sites"

    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_template('utter_confirm_clearwatchlist', tracker)
        clear_watchlist(tracker.sender_id)
        return []
