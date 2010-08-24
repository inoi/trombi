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
import os
import shutil
import subprocess
import time

import nose.tools
import couchdb

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

def teardown():
    global _proc
    _proc.terminate()
    _proc.wait()


def with_couchdb(func):
    @nose.tools.make_decorator(func)
    def inner(*args, **kwargs):
        global baseurl

        # Delete the old database if it exists
        server = couchdb.client.Server(baseurl)
        for database in server:
            del server[database]

        return func(baseurl, *args, **kwargs)

    return inner
