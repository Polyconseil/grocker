#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import sys

import qrcode
import zbarlight


def scan(image):
    return zbarlight.scan_codes('qrcode', image)


def make(content):
    return qrcode.make(content)


def decoded(text):
    return text.decode('utf-8') if isinstance(text, bytes) else text


def identity(content):
    result = scan(make(content))
    if result and len(result) == 1:
        return decoded(result[0])
    else:
        raise RuntimeError('Identity fonction fail !')


def main():
    print(identity(sys.argv[1] if len(sys.argv) > 1 else 'Missing parameter !'))


def custom():
    msg = identity(sys.argv[1] if len(sys.argv) > 1 else 'Missing parameter !')
    print('custom: %s' % msg)

if __name__ == '__main__':
    main()
