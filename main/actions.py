from rasa_core_sdk import Action
from rasa_core_sdk.events import SlotSet

class ActionCheckStatus(Action):
   def name(self):
      # type: () -> Text
      return "action_check_status"

   def run(self, dispatcher, tracker, domain):
      # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict[Text, Any]]
      dispatcher.utter_response('All good')
      return []

class ActionMonitorSite(Action):
   def name(self):
      # type: () -> Text
      return "action_monitor_site"

   def run(self, dispatcher, tracker, domain):
      # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict[Text, Any]]

      return [SlotSet("watch_list", ["https://google.com"])]