#!/usr/bin/env python3
import subprocess
import os
import uuid
from PIL import Image
import imagehash


def getsitehash(url):
    tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
    process = subprocess.run(
        ['utils/screenshot.js', '-u', url, '-o', tempname], stderr=subprocess.STDOUT)
    if process.returncode != 0:
        print(process.stdout)
        return None
    sitehash = str(imagehash.phash(Image.open(tempname)))
    if os.path.isfile(tempname):
        os.remove(tempname)
    return sitehash


print(getsitehash('http://google.com'))
