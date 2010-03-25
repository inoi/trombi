# Copyright (c) Inoi Oy 2010. All rights reserved.
#
# This material constitutes a trade secret of Inoi Oy.
#
# The software, manuals, and technical literature of
# Inoi Oy products may not be reproduced in any form or
# by any means except by permission in writing from
# Inoi Oy.

# Asynchronous CouchDB client
import re
import urllib
import tornado.httpclient
try:
    import json
except ImportError:
    import simplejson as json

import trombi.errors

class Server(object):
    def __init__(self, baseurl, io_loop=None):
        self.baseurl = baseurl
        if self.baseurl[-1] == '/':
            self.baseurl = self.baseurl[:-1]

        self.client = tornado.httpclient.AsyncHTTPClient(io_loop=io_loop)

    def default_errback(self, error, msg):
        raise ValueError(msg)

    def _invalid_db_name(self, name, errback):
        errback(
            trombi.errors.INVALID_DATABASE_NAME,
            'Invalid database name: %r' % name,
            )

    def create(self, name, callback, errback=None):
        errback = errback or self.default_errback

        if not VALID_DB_NAME.match(name):
            # Avoid additional HTTP Query by doing the check here
            self._invalid_db_name(name, errback)
            return

        def _create_callback(response):
            if response.code == 201:
                callback(Database(self, name))
            elif response.code == 412:
                errback(
                    trombi.errors.PRECONDITION_FAILED,
                    'Database already exists: %r' % name
                    )
            else:
                errback(
                    response.code,
                    response.body,
                    )

        self.client.fetch(
            '%s/%s' % (self.baseurl, name),
            _create_callback,
            method='PUT',
            body='',
            )

    def get(self, name, callback, errback=None, create=False):
        errback = errback or self.default_errback
        if not VALID_DB_NAME.match(name):
            return self._invalid_db_name(name, errback)

        def _really_callback(response):
            if response.code == 200:
                callback(Database(self, name))
            elif response.code == 404:
                # Database doesn't exist
                if create:
                    self.create(name, callback, errback)
                else:
                    errback(
                        trombi.errors.NOT_FOUND,
                        'Database not found: %s' % name
                        )

        self.client.fetch(
            '%s/%s' % (self.baseurl, name),
            _really_callback,
            )
    def delete(self, name, callback, errback=None):
        errback = errback or self.default_errback

        def _really_callback(response):
            if response.code == 200:
                callback()
            elif response.code == 404:
                errback(trombi.errors.NOT_FOUND,
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
        self.baseurl = '%s/%s' % (self.server.baseurl, self.name)

    def _fetch(self, url, *args, **kwargs):
        # Just a convenience wrapper
        if 'baseurl' in kwargs:
            url = '%s/%s' % (kwargs.pop('baseurl'), url)
        else:
            url = '%s/%s' % (self.baseurl, url)
        return self.server.client.fetch(url, *args, **kwargs)

    def set(self, data, callback, doc_id=None, errback=None):
        def _really_callback(response):
            try:
                content = json.loads(response.body)
            except ValueError:
                content = response.body
            if response.code == 201:
                doc = Document(
                    self,
                    data.items(),
                    _id=content['id'],
                    _rev=content['rev'],
                    )
                callback(doc)
            elif response.code == 409:
                errback(
                    trombi.errors.CONFLICT,
                    content['reason']
                    )
            else:
                errback(trombi.errors.SERVER_ERROR,
                        response.body)

        if doc_id is not None:
            url = urllib.quote(doc_id, safe='')
            method = 'PUT'
        else:
            url = ''
            method = 'POST'

        self._fetch(
            url,
            _really_callback,
            method=method,
            body=json.dumps(data),
            )

    def get(self, doc_id, callback, errback=None):
        errback = errback or self.server.default_errback

        def _really_callback(response):
            data = json.loads(response.body)
            if response.code == 200:
                doc = Document(self, data.items())
                callback(doc)
            elif response.code == 404:
                # Document doesn't exist
                callback(None)
            else:
                errback(trombi.errors.NOT_FOUND, data['reason'])

        doc_id = urllib.quote(doc_id, safe='')

        self._fetch(
            doc_id,
            _really_callback,
            )

    def view(self, design_doc, viewname, callback, **kwargs):
        errback = kwargs.pop('errback', None) or self.server.default_errback
        def _really_callback(response):
            if response.code == 200:
                callback(json.loads(response.body)['rows'])
            elif response.code == 404:
                errback(trombi.errors.NOT_FOUND,
                         json.loads(response.body)['reason'])
            else:
                errback(trombi.errors.SERVER_ERROR, response.body)

        url = '_design/%s/_view/%s' % (design_doc, viewname)
        if kwargs:
            url = '%s?%s' % (url, urllib.urlencode(kwargs))

        self._fetch(url, _really_callback)

    def delete(self, doc, callback, errback=None):
        errback = errback or self.server.default_errback

        def _really_callback(response):
            try:
                data = json.loads(response.body)
            except ValueError:
                data = response.body

            if response.code == 200:
                callback(self)
            elif response.code == 404:
                errback(trombi.errors.NOT_FOUND, data['reason'])
            elif response.code == 409:
                errback(trombi.errors.CONFLICT, data['reason'])
            else:
                errback(trombi.errors.SERVER_ERROR, data)

        doc_id = urllib.quote(doc.id, safe='')
        self._fetch(
            '%s?rev=%s' % (doc_id, doc.rev),
            _really_callback,
            method='DELETE',
            )


class Document(dict):
    def __init__(self, db, *a, **kw):
        self.db = db
        super(Document, self).__init__(*a, **kw)
        self.id = self.pop('_id')
        self.rev = self.pop('_rev')

    def attach(self, name, data, callback, type='text/plain'):
        def _really_callback(response):
            data = json.loads(response.body)
            assert data['id'] == self.id
            self.rev = data['rev']
            callback(self)

        headers = {'Content-Type': type}

        self.db._fetch(
            '%s/%s?rev=%s' % (self.id, name, self.rev),
            _really_callback,
            method='PUT',
            body=data,
            headers=headers,
            )

    def load_attachment(self, name, callback):
        def _really_callback(response):
            callback(response.body)

        self.db._fetch(
            '%s/%s' % (self.id, name),
            _really_callback,
            )

    def delete_attachment(self, name, callback):
        def _really_callback(response):
            callback(self)

        self.db._fetch(
            '%s/%s?rev=%s' % (self.id, name, self.rev),
            _really_callback,
            method='DELETE',
            )

VALID_DB_NAME = re.compile(r'^[a-z][a-z0-9_$()+-/]*$')
