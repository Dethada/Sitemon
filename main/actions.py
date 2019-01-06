import logging
from rasa_core_sdk import Action
from rasa_core_sdk.events import SlotSet
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
      # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict[Text, Any]]
      # logger.info(tracker.latest_message.text)
      sites = tracker.get_slot('watch_list')
      if not sites:
         sites = []
      new_sites = set(tracker.get_latest_entity_values('url'))

      new_sites = new_sites.union(geturls(tracker.latest_message['text']))
      if sites:
         for site in new_sites:
            if site not in sites:
               sites.append(site)
      else:
         sites = list(new_sites)

      # logger.info('Sites: {}'.format(sites))
      if new_sites:
         dispatcher.utter_message('New sites added to watch list')
         return [SlotSet("watch_list", sites)]
      else:
         dispatcher.utter_message('Please enter an url')
      return []

class ActionStatus(Action):
   def name(self):
      return "action_status"

   def run(self, dispatcher, tracker, domain):
      sites = tracker.get_slot('watch_list')
      
      if sites:
         msg = 'Current watch list\n'
         for index, url in enumerate(sites):
            msg += '{}. {}\n'.format(index+1, url)
      
         dispatcher.utter_message(msg)
      else:
         dispatcher.utter_message('Not watching any sites')

      return []

class ActionRemoveSite(Action):
   def name(self):
      return "action_remove_site"

   def run(self, dispatcher, tracker, domain):
      sites = tracker.get_slot('watch_list')
      remove_sites = set(tracker.get_latest_entity_values('url'))

      remove_sites = remove_sites.union(geturls(tracker.latest_message['text']))
      removedsites = False
      if sites:
         for site in remove_sites:
            if site in sites:
               removedsites = True
               sites.remove(site)

      if removedsites:
         dispatcher.utter_message('Site(s) removed successfully')
      else:
         dispatcher.utter_message('No sites removed')

      return [SlotSet("watch_list", sites if sites else None)]

class ActionRemoveAllSites(Action):
   def name(self):
      return "action_remove_all_sites"

   def run(self, dispatcher, tracker, domain):
      return [SlotSet("watch_list", None)]