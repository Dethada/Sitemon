#!/usr/bin/env python3
from PIL import Image
import imagehash

# pip3 install --user imagehash

prefix = '/tmp/'
hash = imagehash.phash(Image.open('{}/5.png'.format(prefix)))
print(hash)
otherhash = imagehash.phash(Image.open('{}/6.png'.format(prefix)))
print(otherhash)
print(hash == otherhash)
print(hash - otherhash)