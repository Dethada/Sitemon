## Standard path
* start
  - utter_help
* greet
  - utter_greet
* detailed_help
  - utter_detailed_help
* monitor
  - action_monitor_site
* goodbye
  - utter_goodbye

## Standard path 2
* start
  - utter_help
* detailed_help
  - utter_detailed_help
* monitor
  - action_monitor_site
* goodbye
  - utter_goodbye

## Is NSFW
* nsfw_check
  - action_nsfw_check
  
## Monitor Only
* monitor
  - action_monitor_site

## Status Only
* status
  - action_status

## Remove single site
* remove_site
  - action_remove_site

## Really remove all sites
* remove_all_sites
  - utter_confirm_clearwatchlist
* really_remove_sites
  - action_remove_all_sites
  - utter_sites_removed

## Dont remove all sites
* remove_all_sites
  - utter_confirm_clearwatchlist
* abort
  - utter_abort