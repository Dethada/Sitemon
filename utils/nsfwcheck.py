#!/usr/bin/env python3
import os
import argparse
import uuid
import numpy as np
from PIL import Image
import tensorflow as tf

parser = argparse.ArgumentParser(description='Check the category of a site')
parser.add_argument('-u', '--url', help='Url to check', required=True)
parser.add_argument('-k', '--keep', help='Keep image', dest='keep', action='store_true')
parser.set_defaults(keep=False, operation=True)
args = vars(parser.parse_args())

_MODEL_DIR = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '../main/saved_model')

_IMAGE_SIZE = 64
_BATCH_SIZE = 128

_LABEL_MAP = {0: 'drawings', 1: 'hentai', 2: 'neutral', 3: 'porn', 4: 'sexy'}


def standardize(img):
    mean = np.mean(img)
    std = np.std(img)
    img = (img - mean) / std
    return img


def load_image(infilename):
    img = Image.open(infilename)
    img = img.resize((_IMAGE_SIZE, _IMAGE_SIZE))
    img.load()
    data = np.asarray(img, dtype=np.float32)
    data = standardize(data)
    return data


def predict(image_path):
    with tf.Session() as sess:
        graph = tf.get_default_graph()
        tf.saved_model.loader.load(
            sess, [tf.saved_model.tag_constants.SERVING], _MODEL_DIR)
        inputs = graph.get_tensor_by_name("input_tensor:0")
        probabilities_op = graph.get_tensor_by_name('softmax_tensor:0')
        class_index_op = graph.get_tensor_by_name('ArgMax:0')

        image_data = load_image(image_path)
        probabilities, class_index = sess.run([probabilities_op, class_index_op],
                                              feed_dict={inputs: [image_data] * _BATCH_SIZE})

        probabilities_dict = {_LABEL_MAP.get(
            i): l for i, l in enumerate(probabilities[0])}
        pre_label = _LABEL_MAP.get(class_index[0])
        result = {"class": pre_label, "probability": probabilities_dict}
        return result


site = args['url']
tempname = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
os.system('utils/screenshot.js -u \'{}\' -o {}'.format(site, tempname))
if not os.path.isfile(tempname):
    print('An error occured when checking {}\n'.format(site))
    exit(1)
print('{}'.format(tempname))
categorydict = predict(tempname)
print(categorydict)
if not args['keep']:
    print('Removing file')
    os.remove(tempname)
