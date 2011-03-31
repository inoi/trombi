# Copuright (c) 2011 Jyrki Pulliainen <jyrki@dywypi.org>
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
import urllib2

import nose.tools
from tornado.httpclient import HTTPClient

baseurl = ''

def setup():
    global _proc, baseurl
    try:
        shutil.rmtree('tmp')
    except OSError, err:
        if err.errno != errno.ENOENT:
            raise

    os.mkdir('tmp')
    os.mkdir('tmp/couch')

    dbdir = 'tmp/couch'
    ini = 'tmp/local.ini'
    log = 'tmp/couch.log'

    port = 8921
    baseurl = 'http://localhost:%d/' % port

    with open(ini, 'w') as fobj:
        print >>fobj, '''\
[couchdb]
database_dir = %(dbdir)s
view_index_dir = %(dbdir)s

[httpd]
port = %(port)d
bind_address = 127.0.0.1

[log]
file = %(log)s
''' % dict(dbdir=dbdir, log=log, port=port)

    cmdline = 'couchdb -a %s' % ini
    null = open('/dev/null', 'w')
    _proc = subprocess.Popen(cmdline, shell=True, stdout=null, stderr=null)

    # Wait for couchdb to start
    time.sleep(1)
    # Wait for couchdb to start

    while True:
        try:
            f = urllib2.urlopen(baseurl)
        except urllib2.URLError:
            continue
        try:
            data = json.load(f)
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
            dbs = json.loads(response.body)
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
