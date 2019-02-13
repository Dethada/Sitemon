#!/usr/bin/env python3
import subprocess
import os
import uuid
import argparse
from PIL import Image
import imagehash

parser = argparse.ArgumentParser(description='Check the hash of a site')
parser.add_argument('-u','--url', help='Url to check hash of', required=True)
args = vars(parser.parse_args())

def getsitehash(url):
    """
    Gets the perceptual hash of a site

    :param url: the url of the site
    :return: The perceptual hash of the fullpage screen shot of the site or None if it failed
    """
    tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
    os.system('utils/screenshot.js -u \'{}\' -o {}'.format(url, tempname))
    try:
        sitehash = str(imagehash.phash(Image.open(tempname)))
    except FileNotFoundError:
        return None
    if os.path.isfile(tempname):
        os.remove(tempname)
    return sitehash


print(getsitehash('http://google.com'))
