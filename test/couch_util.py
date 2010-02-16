# Copyright (c) Inoi Oy 2010. All rights reserved.
#
# This material constitutes a trade secret of Inoi Oy.
#
# The software, manuals, and technical literature of
# Inoi Oy products may not be reproduced in any form or
# by any means except by permission in writing from
# Inoi Oy.

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
