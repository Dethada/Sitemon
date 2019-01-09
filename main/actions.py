import logging
from rasa_core_sdk import Action
from rasa_core_sdk.events import SlotSet
import re
import sqlite3
from sqlite3 import Error
import requests
import hashlib

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
   except Exception as e:
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