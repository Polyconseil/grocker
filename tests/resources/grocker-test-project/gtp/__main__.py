# Copyright (c) Polyconseil SAS. All rights reserved.


import os.path
import sys
import tempfile

import qrcode
from PIL import Image


def scan(file_path):
    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()
    return image


def make(content):
    return qrcode.make(content)


def identity(content):
    filename = os.path.join(tempfile.mkdtemp(), 'grocker.png')

    image = make(content)
    image.save(filename)

    raw_image = image.get_image()
    read_image = scan(filename)

    if raw_image.tobitmap() == read_image.tobitmap():
        return content
    else:
        raise RuntimeError('Identity function fail !')


def main():
    print(identity(sys.argv[1] if len(sys.argv) > 1 else 'Missing parameter !'))


def custom():
    msg = identity(sys.argv[1] if len(sys.argv) > 1 else 'Missing parameter !')
    print('custom: %s' % msg)


if __name__ == '__main__':
    main()
