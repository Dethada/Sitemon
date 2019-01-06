## intent:greet
- hey
- hello
- hi
- good morning
- good evening
- hey there

## intent:goodbye
- bye
- goodbye
- see you around
- see you later

## intent:monitor
- monitor [google.com](url)
- [http://ai.ai/](url)
- watch [wikipedia.org](url)
- keep an eye on [github.io](url)

## intent:status
- who am i monitoring
- status
- what sites are monitored
- what is my watch list
- show me my watch list

## intent:remove_all_sites
- clear watch list
- remove all sites

## intent:remove_site
- remove [sp.edu.sg](url)
- remove [www.facebook.com](url) from watchlist
- stop monitoring [syzygyy.xyz](url)

## regex:url
- (http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?