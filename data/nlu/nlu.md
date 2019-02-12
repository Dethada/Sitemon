## intent:greet
- hey
- hello
- hi
- good morning
- good evening
- hey there
- greetings
- what's up

## intent:goodbye
- bye
- goodbye
- see you around
- see you later
- exit

## intent:help
- help
- show help
- who are you
- send help

## intent:detailed_help
- tell me more
- what do you do
- what does this bot do
- what are the functions of this bot
- please explain
- how do i monitor a site
- how do i delete a site from my watchlist
- how do i clear my watch list

## intent:nsfw_check
- is [www.google.com](url) nsfw
- i want to know if [http://ai.ai](url) is not safe for work
- check if [facebook.com](url) is nsfw
- is [github.io] not safe for work

## intent:monitor
- monitor [www.google.com](url)
- watch [www.sp.edu.sg](url)
- add [facebook.com](url) to watch list
- check on [http://ai.ai](url)
- keep an eye on [github.io](url)
- i want to add [syzygyy.xyz](url) to my watch list 

## intent:remove_site
- remove [www.sp.edu.sg](url)
- remove [facebook.com](url) from watch list
- delete [http://ai.ai/](url)
- stop monitoring [syzygyy.xyz](url)
- i want to delete [www.google.com](url) from my watchlist
- terminate monitoring for [github.io](url)

## intent:status
- who am i monitoring
- status
- what sites are monitored
- what is my watch list
- show me my watch list
- view watch list
- are there any sites i am monitoring now

## intent:remove_all_sites
- clear watch list
- remove all sites
- delete entire watch list
- empty watch list
- delete all sites
- i want to delete all sites in my watch list

## regex:url
- (http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?
