import logging
from rasa_core_sdk import Action
from rasa_core_sdk.events import SlotSet
import re
import sqlite3
from sqlite3 import Error
import requests
import hashlib
import subprocess
import uuid
import logging
import os
import sys
import numpy as np
from PIL import Image
import operator
import tensorflow as tf

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
db_file = 'database.db'

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None

def process_url(url):
   if not url.startswith('http://') and not url.startswith('https://'):
      url = 'http://' + url
   return url

def get_urls_by_user(username):
   conn = create_connection(db_file)
   cur = conn.cursor()
   cur.execute('SELECT url FROM watchlist WHERE username=?', (username,))
   urls = cur.fetchall()
   conn.close()
   return urls

def insert_url(username, url):
   # requests follows redirects
   try:
      response = requests.get(url)
   except requests.exceptions.RequestException as e:
      logger.info('Exception: {}'.format(e))
      return False
   if response.status_code != 200:
      logger.info('Status: {}'.format(response.status_code))
      return False
   sitehash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()
   conn = create_connection(db_file)
   cur = conn.cursor()
   cur.execute('''INSERT INTO watchlist VALUES (?,?,?,DATETIME('now','localtime'),'false',?)''', (username, url, sitehash, response.status_code))
   conn.commit()
   conn.close()
   return True

def remove_url(username, url):
   conn = create_connection(db_file)
   cur = conn.cursor()
   cur.execute('DELETE FROM watchlist WHERE username=? and url=?', (username,url))
   conn.commit()
   conn.close()

def clear_watchlist(username):
   conn = create_connection(db_file)
   cur = conn.cursor()
   cur.execute('DELETE FROM watchlist WHERE username=?', (username,))
   conn.commit()
   conn.close()

def geturls(text):
   urlregex = re.compile('(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?')

   urls = set()
   for word in text.split(' '):
      match = urlregex.search(word)
      if match:
         urls.add(match.group())

   return urls

_MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'saved_model')

_IMAGE_SIZE = 64
_BATCH_SIZE = 128

_LABEL_MAP = {0:'drawings', 1:'hentai', 2:'neutral', 3:'porn', 4:'sexy'}


def standardize(img):
    mean = np.mean(img)
    std = np.std(img)
    img = (img - mean) / std
    return img

def load_image( infilename ) :
    img = Image.open( infilename )
    img = img.resize((_IMAGE_SIZE, _IMAGE_SIZE))
    img.load()
    data = np.asarray( img, dtype=np.float32 )
    data = standardize(data)
    return data

def predict(image_path):
    with tf.Session() as sess:
        graph = tf.get_default_graph()
        tf.saved_model.loader.load(sess, [tf.saved_model.tag_constants.SERVING], _MODEL_DIR)
        inputs = graph.get_tensor_by_name("input_tensor:0")
        probabilities_op = graph.get_tensor_by_name('softmax_tensor:0')
        class_index_op = graph.get_tensor_by_name('ArgMax:0')

        image_data = load_image(image_path)
        probabilities, class_index = sess.run([probabilities_op, class_index_op],
                                              feed_dict={inputs: [image_data] * _BATCH_SIZE})

        probabilities_dict = {_LABEL_MAP.get(i): l for i, l in enumerate(probabilities[0])}
        pre_label = _LABEL_MAP.get(class_index[0])
        result = {"class": pre_label, "probability": probabilities_dict}
        return result

class ActionNsfwCheck(Action):
   def name(self):
      return "action_nsfw_check"
   def run(self, dispatcher, tracker, domain):
      logging.basicConfig(filename='example.log',level=logging.DEBUG)
      username = tracker.sender_id

      new_sites = set(tracker.get_latest_entity_values('url'))
      new_sites = new_sites.union(geturls(tracker.latest_message['text']))
      p_sites = list(map(process_url, new_sites))
      msg = ''
      if not p_sites:
        dispatcher.utter_message('You have not entered an url or you have entered an url that is already in your watch list.')
      else:
        dispatcher.utter_message('Checking whether sites are nsfw')
        for site in p_sites:
           unique_imgfilepath = '/tmp/' + str(uuid.uuid4()) + '.jpg'
           runjs = subprocess.Popen(['./utils/screenshot.js', '-u',  site, '-o', unique_imgfilepath], stdout=subprocess.PIPE, 
           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
           out, err = runjs.communicate()
           categorydict = predict(unique_imgfilepath)
           maxcategory = categorydict.get('class')
           msg += 'The website belongs to {} category'.format(maxcategory)
           dispatcher.utter_message(msg)
           os.remove(unique_imgfilepath)
      return []

class ActionMonitorSite(Action):
   def name(self):
      # type: () -> Text
      return "action_monitor_site"

   def run(self, dispatcher, tracker, domain):
      username = tracker.sender_id
      logger.info('Sender_id: {}'.format(username))
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
                  msg += 'Failed to add {} to watch list\n'.format(p_site)
      else:
         for site in new_sites:
            p_site = process_url(site)
            if insert_url(username, p_site):
               msg += 'Added {} to watch list\n'.format(p_site)
            else:
               msg += 'Failed to add {} to watch list\n'.format(p_site)

      # logger.info('Sites: {}'.format(sites))
      if msg == '':
         msg = 'You have not entered an url or you have entered an url that is already in your watch list.'
      dispatcher.utter_message(msg)
      return []

class ActionStatus(Action):
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
   def name(self):
      return "action_remove_site"

   def run(self, dispatcher, tracker, domain):
      username = tracker.sender_id
      sites = get_urls_by_user(username)
      logger.info('Sites: {}'.format(sites))
      remove_sites = set(tracker.get_latest_entity_values('url'))

      remove_sites = remove_sites.union(geturls(tracker.latest_message['text']))
      msg = ''
      if sites:
         for site in remove_sites:
            p_site = process_url(site)
            logger.info('Processed Site: {}'.format(p_site))
            if (p_site,) in sites:
               remove_url(username, p_site)
               msg += 'Removed {} from watch list\n'.format(p_site)

      if msg == '':
         msg = 'No sites removed'
      dispatcher.utter_message(msg)

      return [SlotSet("watch_list", sites if sites else None)]

class ActionRemoveAllSites(Action):
   def name(self):
      return "action_remove_all_sites"

   def run(self, dispatcher, tracker, domain):
      clear_watchlist(tracker.sender_id)
      dispatcher.utter_message('Watch list cleared')
      return []
