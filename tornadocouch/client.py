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
                    tornadocouch.errors.PRECONDITION_FAILED,
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

    def delete(self, name, callback, errback=None):
        errback = errback or self.default_errback

        def _really_callback(response):
            if response.code == 200:
                callback()
            elif response.code == 404:
                errback(tornadocouch.errors.NOT_FOUND,
                        'Database does not exist: %r' % name)

        self.client.fetch(
            '%s/%s' % (self.baseurl, name),
            _really_callback,
            method='DELETE',
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

    def create(self, data, callback, doc_id=None, errback=None):
        def _really_callback(response):
            content = json.loads(response.body)
            if response.code == 201:
                doc = Document(_id=content['id'], _rev=content['rev'], **data)
                callback(doc)
            elif response.code == 409:
                errback(
                    tornadocouch.errors.CONFLICT,
                    content['reason']
                    )

        url = '%s/%s' % (self.server.baseurl, self.name)
        if doc_id is not None:
            url = '%s/%s' % (url, doc_id)
            method = 'PUT'
        else:
            method = 'POST'

        self.server.client.fetch(
            url,
            _really_callback,
            method=method,
            body=json.dumps(data),
            )

    def load(self, doc_id, callback, errback=None):
        errback = errback or self.server.default_errback

        def _really_callback(response):
            data = json.loads(response.body)
            if response.code == 200:
                doc = Document(data.items())
                callback(doc)
            elif response.code == 404:
                errback(tornadocouch.errors.NOT_FOUND, data['reason'])

        self.server.client.fetch(
            '%s/%s/%s' % (self.server.baseurl, self.name, doc_id),
            _really_callback,
            )

class Document(dict):
    def __init__(self, *a, **kw):
        super(Document, self).__init__(*a, **kw)
        self.id = self.pop('_id')
        self.rev = self.pop('_rev')

VALID_DB_NAME = re.compile(r'^[a-z][a-z0-9_$()+-/]*$')
