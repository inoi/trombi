# Copyright (c) 2011 Jyrki Pulliainen <jyrki@dywypi.org>
# Copyright (c) 2010 Inoi Oy
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

import errno
import json
import os
import shutil
import subprocess
import time
import sys

try:
    # Python 3
    from urllib import request
    from urllib.error import URLError
except ImportError:
    # Python 3
    import urllib2 as request
    from urllib2 import URLError

import nose.tools
from tornado.httpclient import HTTPClient

baseurl = ''

def setup():
    global _proc, baseurl
    try:
        shutil.rmtree('tmp')
    except OSError:
        # Python 3
        err = sys.exc_info()[1]
        if err.errno != errno.ENOENT:
            raise

    os.mkdir('tmp')
    os.mkdir('tmp/couch')

    dbdir = 'tmp/couch'
    ini = 'tmp/local.ini'
    log = 'tmp/couch.log'

    port = 8921
    baseurl = 'http://localhost:%d/' % port

    cmdline = 'couchdb -n -a test/conf/local.ini'
    null = open('/dev/null', 'w')
    _proc = subprocess.Popen(cmdline, shell=True)#, stdout=null, stderr=null)

    # Wait for couchdb to start
    time.sleep(1)
    # Wait for couchdb to start

    while True:
        try:
            f = request.urlopen(baseurl)
        except URLError:
            continue
        try:
            json.loads(f.read().decode('utf-8'))
        except ValueError:
            continue
        # Got a sensible response
        break

def teardown():
    global _proc
    _proc.terminate()
    _proc.wait()


def with_couchdb(func):
    @nose.tools.make_decorator(func)
    def inner(*args, **kwargs):
        global baseurl

        cli = HTTPClient()
        # Delete all old databases
        response = cli.fetch('%s_all_dbs' % baseurl)
        try:
            dbs = json.loads(response.body.decode('utf-8'))
        except ValueError:
            print >> sys.stderr, \
                "CouchDB's response was invalid JSON: %s" % db_string
            sys.exit(2)

        for database in dbs:
            if database.startswith('_'):
                # Skip special databases like _users
                continue
            cli.fetch(
                '%s%s' % (baseurl, database),
                method='DELETE',
                )

        return func(baseurl, *args, **kwargs)

    return inner
