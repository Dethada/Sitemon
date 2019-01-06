import re

urlregex = re.compile('(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?')

inputfile = ''
outputfile = ''

with open(inputfile, 'r') as f:
    content = f.read().split(' ')


urls = set()
for word in content:
    match = urlregex.search(word)
    if match:
        urls.add(match.group())

# print('\n'.join(urls))
with open(outputfile, 'w') as f:
    f.write('\n'.join(urls))