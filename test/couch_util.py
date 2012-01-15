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


_couch_1_1_user_view = """
(
    function(newDoc, oldDoc, userCtx) {
        if (newDoc._deleted === true) {
            // allow deletes by admins and matching users
            // without checking the other fields
            if ((userCtx.roles.indexOf('_admin') !== -1) ||
                (userCtx.name == oldDoc.name)) {
                return;
            } else {
                throw({forbidden: 'Only admins may delete other user docs.'});
            }
        }

        if ((oldDoc && oldDoc.type !== 'user') || newDoc.type !== 'user') {
            throw({forbidden : 'doc.type must be user'});
        } // we only allow user docs for now

        if (!newDoc.name) {
            throw({forbidden: 'doc.name is required'});
        }

        if (newDoc.roles && !isArray(newDoc.roles)) {
            throw({forbidden: 'doc.roles must be an array'});
        }

        if (newDoc._id !== ('org.couchdb.user:' + newDoc.name)) {
            throw({
                forbidden: 'Doc ID must be of the form org.couchdb.user:name'
            });
        }

        if (oldDoc) { // validate all updates
            if (oldDoc.name !== newDoc.name) {
                throw({forbidden: 'Usernames can not be changed.'});
            }
        }

        if (newDoc.password_sha && !newDoc.salt) {
            throw({
                forbidden: 'Users with password_sha must have a salt.' +
                    'See /_utils/script/couch.js for example code.'
            });
        }

        if (userCtx.roles.indexOf('_admin') === -1) {
            if (oldDoc) { // validate non-admin updates
                if (userCtx.name !== newDoc.name) {
                    throw({
                        forbidden: 'You may only update your own user document.'
                    });
                }
                // validate role updates
                var oldRoles = oldDoc.roles.sort();
                var newRoles = newDoc.roles.sort();

                if (oldRoles.length !== newRoles.length) {
                    throw({forbidden: 'Only _admin may edit roles'});
                }

                for (var i = 0; i < oldRoles.length; i++) {
                    if (oldRoles[i] !== newRoles[i]) {
                        throw({forbidden: 'Only _admin may edit roles'});
                    }
                }
            } else if (newDoc.roles.length > 0) {
                throw({forbidden: 'Only _admin may set roles'});
            }
        }

        // no system roles in users db
        for (var i = 0; i < newDoc.roles.length; i++) {
            if (newDoc.roles[i][0] === '_') {
                throw({
                    forbidden:
                    'No system roles (starting with underscore) in users db.'
                });
            }
        }

        // no system names as names
        if (newDoc.name[0] === '_') {
            throw({forbidden: 'Username may not start with underscore.'});
        }
    }
)
"""


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

        # Update _auth with parenthesis, in case we are running too
        # new spidermonkey, which fails in evaluation

        user_auth_doc = json.loads(
            cli.fetch('%s/_users/_design/_auth' % baseurl).body
        )

        user_auth_doc['validate_doc_update'] = _couch_1_1_user_view

        try:
            response = cli.fetch('%s_session' % baseurl,
                  headers={
                      'Content-Type': 'application/x-www-form-urlencoded',
                  },
                  method='POST',
                  body='name=admin&password=admin',
            )
            cookie = response.headers['Set-Cookie']
        except HTTPError:
            cookie = ''

        cli.fetch(
            '%s/_users/_design/_auth/' % baseurl,
            body=json.dumps(user_auth_doc),
            method='PUT',
            headers={'Cookie': cookie},
        )

        return func(baseurl, *args, **kwargs)

    return inner
