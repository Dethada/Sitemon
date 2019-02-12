#!/usr/bin/env python3
from PIL import Image
import imagehash
import argparse

# pip3 install --user imagehash

parser = argparse.ArgumentParser(description='Get the perceptual hash of an image')
parser.add_argument('-f','--file', help='File to be hashed', required=True)
args = vars(parser.parse_args())

hash = imagehash.phash(Image.open(args['file']))
print(hash)
# otherhash = imagehash.phash(Image.open('{}/6.png'.format(prefix)))
# print(otherhash)
# print(hash == otherhash)
# print(hash - otherhash)
# print(type(hash))