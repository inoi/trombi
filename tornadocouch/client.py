# Asynchronous CouchDB client
import re
import tornado.httpclient
try:
    import json
except ImportError:
    import simplejson as json

import tornadocouch.errors

class Server(object):
    def __init__(self, baseurl, io_loop=None):
        self.baseurl = baseurl
        if self.baseurl[-1] == '/':
            self.baseurl = self.baseurl[:-1]

        self.client = tornado.httpclient.AsyncHTTPClient(io_loop=io_loop)

    def default_errback(self, error, msg):
        raise ValueError(msg)

    def create(self, name, callback, errback=None):
        errback = errback or self.default_errback

        if not VALID_DB_NAME.match(name):
            # Avoid additional HTTP Query by doing the check here
            errback(
                tornadocouch.errors.INVALID_DATABASE_NAME,
                'Invalid database name: %r' % name,
                )
            return

        def _create_callback(response):
            if response.code == 201:
                callback(Database(self, name))
            elif response.code == 412:
                errback(
                    tornadocouch.errors.ALREADY_EXISTS,
                    'Database already exists: %r' % name
                    )
            else:
                response.code(
                    funrniture.errors.GENERIC,
                    response.body,
                    )

        self.client.fetch(
            '%s/%s' % (self.baseurl, name),
            _create_callback,
            method='PUT',
            body='',
            )

    def list(self, callback, errback=None):
        errback = errback or self.default_errback
        def _really_callback(response):
            if response.code == 200:
                callback(Database(self, x) for x in json.loads(response.body))
            else:
                errback(response)

        self.client.fetch(
            '%s/%s' % (self.baseurl, '_all_dbs'),
            _really_callback,
            )

class Database(object):
    def __init__(self, server, name=None):
        self.server = server
        self.name = name

    def delete(self, callback, errback=None):
        errback = errback or self.server.default_errback

        def _really_callback(response):
            if response.code == 200:
                callback()
            elif response.code == 404:
                errback(tornadocouch.errors.DOES_NOT_EXIST,
                        'Database does not exist: %r' % self.name)

        self.server.client.fetch(
            '%s/%s' % (self.server.baseurl, self.name),
            _really_callback,
            method='DELETE',
            body='',
            )


VALID_DB_NAME = re.compile(r'^[a-z][a-z0-9_$()+-/]*$')
