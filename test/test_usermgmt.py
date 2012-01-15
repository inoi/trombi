#
# Copyright (c) 2011 Daniel Truemper truemped@googlemail.com
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#

from __future__ import with_statement

from datetime import datetime
import hashlib
import sys

from nose.tools import eq_ as eq
from .couch_util import setup, teardown, with_couchdb
from .util import with_ioloop, DatetimeEncoder

try:
    import json
except ImportError:
    import simplejson as json

try:
    # Python 3
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib2 import HTTPError

import trombi
import trombi.errors


@with_ioloop
@with_couchdb
def test_add_user(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def callback(doc):
        assert not doc.error
        ioloop.stop()

    s.add_user('test', 'test', callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_get_user(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def callback(doc):
        assert not doc.error
        ioloop.stop()

    s.add_user('get_test', 'test', callback)
    ioloop.start()

    user = []
    def callback(doc):
        assert not doc.error
        user.append(doc)
        ioloop.stop()

    s.get_user('get_test', callback)
    ioloop.start()

    eq(True, isinstance(user[0], trombi.Document))

@with_ioloop
@with_couchdb
def test_update_user(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)
    userdoc = []

    def add_callback(doc):
        assert not doc.error
        userdoc.append(doc)
        ioloop.stop()

    s.add_user('updatetest', 'test', add_callback)
    ioloop.start()

    def update_callback(doc):
        assert not doc.error
        userdoc.append(doc)
        ioloop.stop()

    userdoc[0]['roles'].append('test')
    s.update_user(userdoc[0], update_callback)
    ioloop.start()

    eq(userdoc[1]['roles'], ['test'])

    def update_passwd_callback(doc):
        assert not doc.error
        userdoc.append(doc)
        ioloop.stop()

    s.update_user_password('updatetest', 'test2', update_passwd_callback)
    ioloop.start()

    eq(userdoc[1]['salt'], userdoc[2]['salt'])
    eq(userdoc[1]['password_sha'] != userdoc[2]['password_sha'], True)


@with_ioloop
@with_couchdb
def test_delete_user(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)
    user = []

    def add_callback(doc):
        assert not doc.error
        user.append(doc)
        ioloop.stop()

    s.add_user('deletetest', 'test', add_callback)
    ioloop.start()

    def delete_callback(db):
        assert not db.error
        assert isinstance(db, trombi.Database)
        ioloop.stop()

    s.delete_user(user[0], delete_callback)
    ioloop.start()
