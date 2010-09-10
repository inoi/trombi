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

"""Asynchronous CouchDB client"""

import re
import urllib
import collections

from base64 import b64encode, b64decode
from tornado.httpclient import AsyncHTTPClient
try:
    import json
except ImportError:
    import simplejson as json

import trombi.errors

def from_uri(uri, fetch_args={}, io_loop=None):
    import urlparse

    p = urlparse.urlparse(uri)
    if p.params or p.query or p.fragment:
        raise ValueError('Invalid database address: %s (extra query params)' % uri)
    if p.scheme != 'http':
        raise ValueError('Invalid database address: %s (only http:// is supported)' % uri)

    baseurl = urlparse.urlunsplit((p.scheme, p.netloc, '', '', ''))
    server = Server(baseurl, fetch_args, io_loop=io_loop)

    db_name = p.path.lstrip('/').rstrip('/')
    return Database(server, db_name)


class TrombiError(object):
    def __init__(self, errno, msg):
        self.error = True
        self.errno = errno
        self.msg = msg

    def __str__(self):
        return 'CouchDB reported an error: %s (%d)' % (self.msg, self.errno)


class TrombiObject(object):
    """
    Dummy result for queries that really don't have anything sane to
    return, like succesful database deletion.

    """
    error = False

class TrombiResult(TrombiObject):
    """
    A generic result objects for Trombi queries that do not have any
    formal representation.
    """

    def __init__(self, data):
        self.content = data
        super(TrombiResult, self).__init__()


def _jsonize_params(params):
    for key, value in params.iteritems():
        params[key] = json.dumps(value)
    return urllib.urlencode(params)


def _error_response(response):
    if response.code == 599:
        return TrombiError(599, 'Unable to connect to CouchDB')

    try:
        content = json.loads(response.body)
    except ValueError:
        return TrombiError(response.code, response.body)
    try:
        return TrombiError(response.code, content['reason'])
    except (KeyError, TypeError):
        # TypeError is risen if the result is a list
        return TrombiError(response.code, content)

class Server(TrombiObject):
    def __init__(self, baseurl, fetch_args={}, io_loop=None):
        self.error = False
        self.baseurl = baseurl
        if self.baseurl[-1] == '/':
            self.baseurl = self.baseurl[:-1]
        self._fetch_args = fetch_args
        self.io_loop = io_loop

    def _invalid_db_name(self, name):
        return TrombiError(
            trombi.errors.INVALID_DATABASE_NAME,
            'Invalid database name: %r' % name,
            )

    def _fetch(self, *args, **kwargs):
        # just a convenince wrapper
        kwargs.update(self._fetch_args)
        AsyncHTTPClient(io_loop=self.io_loop).fetch(*args, **kwargs)

    def create(self, name, callback):
        if not VALID_DB_NAME.match(name):
            # Avoid additional HTTP Query by doing the check here
            callback(self._invalid_db_name(name))

        def _create_callback(response):
            if response.code == 201:
                callback(Database(self, name))
            elif response.code == 412:
                callback(
                    TrombiError(
                        trombi.errors.PRECONDITION_FAILED,
                        'Database already exists: %r' % name
                        ))
            else:
                callback(_error_response(response))

        self._fetch(
            '%s/%s' % (self.baseurl, name),
            _create_callback,
            method='PUT',
            body='',
            )

    def get(self, name, callback, create=False):
        if not VALID_DB_NAME.match(name):
            callback(self._invalid_db_name(name))

        def _really_callback(response):
            if response.code == 200:
                callback(Database(self, name))
            elif response.code == 404:
                # Database doesn't exist
                if create:
                    self.create(name, callback)
                else:
                    callback(TrombiError(
                            trombi.errors.NOT_FOUND,
                            'Database not found: %s' % name
                            ))
            else:
                callback(_error_response(response))

        self._fetch(
            '%s/%s' % (self.baseurl, name),
            _really_callback,
            )
    def delete(self, name, callback):

        def _really_callback(response):
            if response.code == 200:
                callback(TrombiObject())
            elif response.code == 404:
                callback(
                    TrombiError(
                        trombi.errors.NOT_FOUND,
                        'Database does not exist: %r' % name
                        ))
            else:
                callback(_error_response(response))

        self._fetch(
            '%s/%s' % (self.baseurl, name),
            _really_callback,
            method='DELETE',
            body='',
            )

    def list(self, callback):
        def _really_callback(response):
            if response.code == 200:
                callback(Database(self, x) for x in json.loads(response.body))
            else:
                callback(_error_response(response))

        self._fetch(
            '%s/%s' % (self.baseurl, '_all_dbs'),
            _really_callback,
            )

class Database(TrombiObject):
    def __init__(self, server, name):
        self.server = server
        self.name = name
        self.baseurl = '%s/%s' % (self.server.baseurl, self.name)

    def _fetch(self, url, *args, **kwargs):
        # Just a convenience wrapper
        if 'baseurl' in kwargs:
            url = '%s/%s' % (kwargs.pop('baseurl'), url)
        else:
            url = '%s/%s' % (self.baseurl, url)
        return self.server._fetch(url, *args, **kwargs)

    def set(self, *args, **kwargs):
        if len(args) == 2:
            data, callback = args
            doc_id = None
        elif len(args) == 3:
            doc_id, data, callback = args
        else:
            raise TypeError(
                'Database.set expected 2 or 3 arguments, got %d' % len(args))

        if kwargs:
            if kwargs.keys() != ['attachments']:
                if len(kwargs) > 1:
                    raise TypeError(
                        '%s are invalid keyword arguments for this function') %(
                        (', '.join(kwargs.keys())))
                else:
                    raise TypeError(
                        '%s is invalid keyword argument for this function' % (
                            kwargs.keys()[0]))

            attachments = kwargs['attachments']
        else:
            attachments = {}

        if isinstance(data, Document):
            doc = data
        else:
            doc = Document(self, data)

        if doc_id is None and doc.id is not None and doc.rev is not None:
            # Update the existing document
            doc_id = doc.id

        if doc_id is not None:
            url = urllib.quote(doc_id, safe='')
            method = 'PUT'
        else:
            url = ''
            method = 'POST'


        for name, attachment in attachments.items():
            content_type, attachment_data = attachment
            if content_type is None:
                content_type = 'text/plain'
            doc.attachments[name] = {
                'content_type': content_type,
                'data': b64encode(attachment_data),
                }

        def _really_callback(response):
            try:
                content = json.loads(response.body)
            except ValueError:
                content = response.body

            if response.code == 201:
                doc.id = content['id']
                doc.rev = content['rev']
                callback(doc)
            else:
                callback(_error_response(response))

        self._fetch(
            url,
            _really_callback,
            method=method,
            body=json.dumps(doc._as_dict()),
            )

    def get(self, doc_id, callback, attachments=False):
        def _really_callback(response):
            data = json.loads(response.body)
            if response.code == 200:
                doc = Document(self, data)
                callback(doc)
            elif response.code == 404:
                # Document doesn't exist
                callback(None)
            else:
                callback(_error_response(response))

        doc_id = urllib.quote(doc_id, safe='')

        if attachments is True:
            doc_id += '?attachments=true'

        self._fetch(
            doc_id,
            _really_callback,
            )

    def view(self, design_doc, viewname, callback, **kwargs):
        def _really_callback(response):
            if response.code == 200:
                callback(
                    ViewResult(json.loads(response.body))
                    )
            else:
                callback(_error_response(response))

        url = '_design/%s/_view/%s' % (design_doc, viewname)
        if kwargs:
            url = '%s?%s' % (url, _jsonize_params(kwargs))

        self._fetch(url, _really_callback)

    def list(self, design_doc, listname, viewname, callback, **kwargs):
        def _really_callback(response):
            if response.code == 200:
                callback(TrombiResult(response.body))
            else:
                callback(_error_response(response))

        url = '_design/%s/_list/%s/%s/' % (design_doc, listname, viewname)
        if kwargs:
            url = '%s?%s' % (url, _jsonize_params(kwargs))

        self._fetch(url, _really_callback)

    def temporary_view(self, callback, map_fun, reduce_fun=None,
                       language='javascript', **kwargs):
        def _really_callback(response):
            if response.code == 200:
                callback(
                    ViewResult(json.loads(response.body))
                    )
            else:
                callback(_error_response(response))

        url = '_temp_view'
        if kwargs:
            url = '%s?%s' % (url, _jsonize_params(kwargs))

        body = {'map': map_fun, 'language': language}
        if reduce_fun:
            body['reduce'] = reduce_fun

        self._fetch(url, _really_callback, method='POST',
                    body=json.dumps(body),
                    headers={'Content-Type': 'application/json'})

    def delete(self, doc, callback):
        def _really_callback(response):
            try:
                data = json.loads(response.body)
            except ValueError:
                callback(_error_response(response))
                return
            if response.code == 200:
                callback(self)
            else:
                callback(_error_response(response))

        doc_id = urllib.quote(doc.id, safe='')
        self._fetch(
            '%s?rev=%s' % (doc_id, doc.rev),
            _really_callback,
            method='DELETE',
            )


class Document(collections.MutableMapping, TrombiObject):
    def __init__(self, db, data):
        self.db = db
        self.data = {}
        self.id = None
        self.rev = None
        self._postponed_attachments = False
        self.attachments = {}

        for key, value in data.items():
            if key.startswith('_'):
                setattr(self, key[1:], value)
            else:
                self[key] = value

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if key.startswith('_'):
            raise KeyError("Keys starting with '_' are reserved for CouchDB")
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def _as_dict(self):
        result = {}
        if self.id:
            result['_id'] = self.id
        if self.rev:
            result['_rev'] = self.rev
        if self.attachments:
            result['_attachments'] = self.attachments

        result.update(self.data)
        return result

    def copy(self, new_id, callback):
        assert self.rev and self.id

        def _copy_done(response):
            if response.code != 201:
                callback(_error_response(response))
                return

            content = json.loads(response.body)
            doc = Document(self.db, self.data)
            doc.attachments = self.attachments.copy()
            doc.id = content['id']
            doc.rev = content['rev']
            callback(doc)

        self.db._fetch(
            '%s' % urllib.quote(self.id, safe=''),
            _copy_done,
            allow_nonstandard_methods=True,
            method='COPY',
            headers={'Destination': str(new_id)}
            )

    def attach(self, name, data, callback, type='text/plain'):
        def _really_callback(response):
            data = json.loads(response.body)
            assert data['id'] == self.id
            self.rev = data['rev']
            callback(self)

        headers = {'Content-Type': type, 'Expect': ''}

        doc_id = urllib.quote(self.id)

        self.db._fetch(
            '%s/%s?rev=%s' % (
                urllib.quote(self.id, safe=''),
                urllib.quote(name, safe=''),
                self.rev),
            _really_callback,
            method='PUT',
            body=data,
            headers=headers,
            )

    def load_attachment(self, name, callback):
        def _really_callback(response):
            if response.code == 200:
                callback(response.body)
            else:
                callback(_error_response(response))

        if (hasattr(self, 'attachments') and
            name in self.attachments and
            not self.attachments[name].get('stub', False)):
            callback(b64decode(self.attachments[name]['data']))
        else:
            self.db._fetch(
                '%s/%s' % (
                    urllib.quote(self.id, safe=''),
                    urllib.quote(name, safe='')
                    ),
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

class ViewResult(TrombiObject, collections.Sequence):
    def __init__(self, result):
        self._total_rows = result.get('total_rows', len(result['rows']))
        self._rows = result['rows']

    def __len__(self):
        return self._total_rows

    def __iter__(self):
        return iter(self._rows)

    def __getitem__(self, key):
        return self._rows[key]



VALID_DB_NAME = re.compile(r'^[a-z][a-z0-9_$()+-/]*$')
