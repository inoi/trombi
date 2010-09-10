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

from __future__ import with_statement

from nose.tools import eq_ as eq
from couch_util import setup, teardown, with_couchdb
from util import with_ioloop, assert_raises

try:
    import json
except ImportError:
    import simplejson as json
import urllib
import functools

import trombi
import trombi.errors

def test_from_uri():
    db = trombi.from_uri('http://1.2.3.4/foobar')
    assert isinstance(db.server, trombi.Server)
    eq(db.baseurl, 'http://1.2.3.4/foobar')
    eq(db.name, 'foobar')

    db = trombi.from_uri('http://1.2.3.4:1122/foobar/')
    assert isinstance(db.server, trombi.Server)
    eq(db.baseurl, 'http://1.2.3.4:1122/foobar')
    eq(db.name, 'foobar')

@with_ioloop
def test_cannot_connect(ioloop):
    def create_callback(db):
        eq(db.error, True)
        eq(db.errno, 599)
        eq(db.msg, 'Unable to connect to CouchDB')
        ioloop.stop()

    s = trombi.Server('http://localhost:39998', io_loop=ioloop)
    s.create('couchdb-database', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_db(baseurl, ioloop):
    def create_callback(db):
        eq(db.error, False)
        assert isinstance(db, trombi.Database)
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), [db.name])
        ioloop.stop()


    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('couchdb-database', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_db_exists(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def first_callback(db):
        s.create(
            'couchdb-database',
            callback=callback,
            )

    def callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.PRECONDITION_FAILED)
        eq(result.msg, "Database already exists: 'couchdb-database'")
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), ['couchdb-database'])
        ioloop.stop()

    s.create('couchdb-database', callback=first_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_invalid_db_name(baseurl, ioloop):
    def callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.INVALID_DATABASE_NAME)
        eq(result.msg, "Invalid database name: 'this name is invalid'")
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('this name is invalid', callback=callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_get_create_doesnt_yet_exist(baseurl, ioloop):
    def callback(db):
        eq(db.error, False)
        eq(db.name, 'nonexistent')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.get('nonexistent', create=True, callback=callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_get_create_already_exists(baseurl, ioloop):
    def create_callback(db):
        eq(db.name, 'new')
        s.get('new', create=True, callback=get_callback)

    def get_callback(db):
        eq(db.error, False)
        eq(db.name, 'new')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('new', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_db(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)
    def create_callback(db):
        s.delete('testdatabase', callback=delete_callback)

    def delete_callback(result):
        eq(result.error, False)
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), [])
        ioloop.stop()

    s.create('testdatabase', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_db_not_exists(baseurl, ioloop):
    def callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.NOT_FOUND)
        eq(result.msg, "Database does not exist: 'testdatabase'")
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.delete('testdatabase', callback=callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_list_databases(baseurl, ioloop):
    def create_first(db):
        s.create('testdb2', callback=create_second)

    def create_second(db):
        s.list(callback=list_callback)

    def list_callback(databases):
        databases = list(databases)
        assert all(isinstance(x, trombi.Database) for x in databases)
        eq(
            set(['testdb2', 'testdb1']),
            set([x.name for x in databases]),
            )
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb1', callback=create_first)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_database(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def create_callback(db):
        s.get('testdb1', callback=get_callback)

    def get_callback(db):
        eq(db.error, False)
        eq(db.name, 'testdb1')
        eq(db.server, s)
        ioloop.stop()

    s.create('testdb1', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_nonexisting_database(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.NOT_FOUND)
        eq(result.msg, "Database not found: testdb1")
        ioloop.stop()

    s.get('testdb1', callback=callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_database_bad_name(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.INVALID_DATABASE_NAME)
        eq(result.msg, "Invalid database name: 'not a valid name'")
        ioloop.stop()

    s.get('not a valid name', callback=callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_document(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        eq(doc.error, False)
        assert isinstance(doc, trombi.Document)
        assert doc.id
        assert doc.rev

        eq(doc['testvalue'], 'something')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_document_with_slash(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'something/with/slash',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        eq(doc.error, False)
        assert isinstance(doc, trombi.Document)
        assert doc.id
        assert doc.rev

        eq(doc.id, 'something/with/slash')
        eq(doc['testvalue'], 'something')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_get_document(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            db.get(doc.id, callback=get_doc_callback)

        def get_doc_callback(doc):
            eq(doc.error, False)
            assert isinstance(doc, trombi.Document)
            assert doc.id
            assert doc.rev

            eq(doc['testvalue'], 'something')
            ioloop.stop()

        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_get_document_with_attachments(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            db.get(doc.id, callback=get_doc_callback, attachments=True)

        def get_doc_callback(doc):
            assert isinstance(doc, trombi.Document)
            assert doc.id
            assert doc.rev

            eq(doc['testvalue'], 'something')

            def _assert_on_fetch(*a, **kw):
                assert False, 'Fetch detected, failing test!'

            doc.db._fetch = _assert_on_fetch

            doc.load_attachment('foo', got_attachment)

        def got_attachment(data):
            eq(data, 'bar')
            ioloop.stop()

        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            attachments={'foo': (None, 'bar')}
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_create_document_custom_id(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            eq(doc.error, False)
            assert isinstance(doc, trombi.Document)
            eq(doc.id, 'testid')
            assert '_id' not in doc
            assert '_rev' not in doc
            assert doc.rev

            eq(doc['testvalue'], 'something')

            f = urllib.urlopen('%stestdb/testid' % baseurl)
            eq(json.load(f),
               {'_id': 'testid',
                '_rev': doc.rev,
                'testvalue': 'something',
                })
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_document(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            eq(db.error, False)
            db.delete(doc, callback=delete_doc_callback)

        def delete_doc_callback(db):
            eq(db.error, False)
            assert isinstance(db, trombi.Database)
            ioloop.stop()

            f = urllib.urlopen('%stestdb/testid' % baseurl)
            eq(f.getcode(), 404)

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_document_not_existing(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            doc.id = 'wrongid'
            db.delete(doc, callback=delete_doc_errback)

        def delete_doc_errback(response):
            eq(response.error, True)
            eq(response.errno, trombi.errors.NOT_FOUND)
            eq(response.msg, 'missing')
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_delete_document_wrong_rev(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            doc.rev = '1-eabf'
            db.delete(doc, callback=delete_doc_callback)

        def delete_doc_callback(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.CONFLICT)
            eq(result.msg, 'Document update conflict.')
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_document_invalid_rev(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            doc.rev = 'invalid'
            db.delete(doc, callback=delete_doc_callback)

        def delete_doc_callback(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.BAD_REQUEST)
            eq(result.msg, 'Invalid rev format')
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_document_custom_id_exists(baseurl, ioloop):
    def do_test(db):
        def create_doc_callback(doc):
            db.set(
                'testid',
                {'testvalue': 'something'},
                update_doc_error,
                )

        def update_doc_error(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.CONFLICT)
            eq(result.msg, 'Document update conflict.')
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_update_document(baseurl, ioloop):
    def do_test(db):
        def update_doc(doc):
            doc['newvalue'] = 'somethingelse'
            db.set(doc, doc_updated)

        def doc_updated(doc):
            eq(doc, {
                'testvalue': 'something',
                'newvalue': 'somethingelse',
            })
            ioloop.stop()

        db.set(
            'testid',
            {'testvalue': 'something'},
            update_doc,
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_set_document_change_id(baseurl, ioloop):
    def do_test(db):
        def update_doc(doc):
            doc['newvalue'] = 'somethingelse'
            db.set('otherid', doc, doc_updated)

        def doc_updated(doc):
            eq(doc, {
                'testvalue': 'something',
                'newvalue': 'somethingelse',
            })
            eq(doc.id, 'otherid')

            # Check that the original didn't change
            db.get('testid', check_original)

        def check_original(doc):
            eq(doc, {'testvalue': 'something'})
            eq(doc.id, 'testid')
            ioloop.stop()

        db.set('testid', {'testvalue': 'something'}, update_doc)

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_get_document_does_not_exist(baseurl, ioloop):
    def create_db_callback(db):
        db.get('foo', callback=get_callback)

    def get_callback(doc):
        eq(doc, None)
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_save_attachment_inline(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            data_callback,
            attachments={'foobar': (None, 'some textual data')},
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.attach('foobar', data, callback=data_callback)

    def data_callback(doc):
        f = urllib.urlopen('%stestdb/testid/foobar' % baseurl)
        eq(f.read(), 'some textual data')
        ioloop.stop()



    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_save_attachment_inline_custom_content_type(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            data_callback,
            attachments={'foobar':
                             ('application/x-custom', 'some textual data')
                         },
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.attach('foobar', data, callback=data_callback)

    def data_callback(doc):
        f = urllib.urlopen('%stestdb/testid/foobar' % baseurl)
        eq(f.info()['Content-Type'], 'application/x-custom')
        eq(f.read(), 'some textual data')
        ioloop.stop()



    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_save_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.attach('foobar', data, callback=data_callback)

    def data_callback(doc):
        f = urllib.urlopen('%stestdb/testid/foobar' % baseurl)
        eq(f.read(), 'some textual data')
        ioloop.stop()



    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.attach('foobar', data, callback=attach_callback)

    def attach_callback(doc):
        doc.load_attachment('foobar', callback=data_callback)

    def data_callback(data):
        eq(data, 'some textual data')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_unkonwn_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.load_attachment('foobar', callback=data_callback)

    def data_callback(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.NOT_FOUND)
        eq(result.msg, 'Document is missing attachment')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_inline_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            attach_callback,
            attachments={'foobar': (None, 'some textual data')},
            )

    def attach_callback(doc):
        doc.load_attachment('foobar', callback=data_callback)

    def data_callback(data):
        eq(data, 'some textual data')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_inline_attachment_no_fetch(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            attach_callback,
            attachments={'foobar': (None, 'some textual data')},
            )

    def attach_callback(doc):
        def _broken_fetch(*a, **kw):
            assert False, 'Fetch called when not needed!'

        doc.db._fetch = _broken_fetch
        doc.load_attachment('foobar', callback=data_callback)

    def data_callback(data):
        eq(data, 'some textual data')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_delete_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            'testid',
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        data = 'some textual data'
        doc.attach('foobar', data, callback=attach_callback)

    def attach_callback(doc):
        doc.delete_attachment('foobar', callback=delete_callback)

    def delete_callback(doc):
        f = urllib.urlopen('%stestdb/testid/foobar' % baseurl)
        eq(f.getcode(), 404)
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_view_empty_results(baseurl, ioloop):
    def do_test(db):
        def create_view_callback(response):
            eq(response.code, 201)
            db.view('testview', 'all', load_view_cb)

        def load_view_cb(result):
            assert isinstance(result, trombi.ViewResult)
            eq(result.error, False)
            eq(len(result), 0)
            ioloop.stop()

        db.server._fetch(
            '%stestdb/_design/testview' % baseurl,
            create_view_callback,
            method='PUT',
            body=json.dumps(
                {
                    'language': 'javascript',
                    'views': {
                        'all': {
                            'map': 'function (doc) { emit(null, doc) }',
                            }
                        }
                    }
                )
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_view_with_results(baseurl, ioloop):
    def do_test(db):
        def create_view_callback(response):
            eq(response.code, 201)
            db.set({'data': 'data'}, create_doc_cb)

        def create_doc_cb(doc):
            db.view('testview', 'all', load_view_cb)

        def load_view_cb(result):
            eq(result.error, False)
            eq(len(result), 1)
            del result[0]['value']['_rev']
            del result[0]['value']['_id']
            del result[0]['id']
            eq(list(result), [{'value': {'data': 'data'}, 'key': None}])
            ioloop.stop()

        db.server._fetch(
            '%stestdb/_design/testview' % baseurl,
            create_view_callback,
            method='PUT',
            body=json.dumps(
                {
                    'language': 'javascript',
                    'views': {
                        'all': {
                            'map': 'function (doc) { emit(null, doc) }',
                            }
                        }
                    }
                )
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_view_with_grouping_reduce(baseurl, ioloop):
    def do_test(db):
        def create_view_callback(response):
            eq(response.code, 201)
            db.set({'data': 'data'}, create_1st_doc_cb)

        def create_1st_doc_cb(doc):
            db.set({'data': 'other'}, create_2nd_doc_cb)

        def create_2nd_doc_cb(doc):
            db.view('testview', 'all', load_view_cb, group=True)

        def load_view_cb(result):
            eq(result.error, False)
            eq(list(result), [{'value': 1, 'key': 'data'},
                              {'value': 1, 'key': 'other'}])
            ioloop.stop()

        db.server._fetch(
            '%stestdb/_design/testview' % baseurl,
            create_view_callback,
            method='PUT',
            body=json.dumps(
                {
                    'language': 'javascript',
                    'views': {
                        'all': {
                            'map': 'function (doc) { emit(doc.data, doc) }',
                            'reduce': 'function (key, value) { return \
                                       value.length }',
                            }
                        }
                    }
                )
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_view_no_design_doc(baseurl, ioloop):
    def create_db_callback(db):
        def load_view_cb(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.NOT_FOUND)
            eq(result.msg, 'missing')
            ioloop.stop()
        db.view('testview', 'all', load_view_cb, group='true')


    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_view_no_such_view(baseurl, ioloop):
    def do_test(db):
        def create_view_callback(useless):
            db.view('testview', 'all', load_view_cb)

        def load_view_cb(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.NOT_FOUND)
            eq(result.msg, 'missing_named_view')
            ioloop.stop()

        db.server._fetch(
            '%stestdb/_design/testview' % baseurl,
            create_view_callback,
            method='PUT',
            body=json.dumps(
                {
                    'language': 'javascript',
                    'views': {
                        'foobar': {
                            'map': 'function (doc) { emit(doc.data, doc) }',
                            'reduce': 'function (key, value) { return \
                                       value.length }',
                            }
                        }
                    }
                )
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_temporary_view_empty_results(baseurl, ioloop):
    def create_db_callback(db):
        db.temporary_view(view_results, 'function(doc) { emit(null, doc); }')

    def view_results(result):
        assert isinstance(result, trombi.ViewResult)
        eq(result.error, False)
        eq(list(result), [])
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_temporary_view_no_such_db(baseurl, ioloop):
    def view_results(result):
        eq(result.error, True)
        eq(result.errno, trombi.errors.NOT_FOUND)
        eq(result.msg, 'no_db_file')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    db = trombi.Database(s, 'doesnotexist')
    db.temporary_view(view_results, 'function() { emit(null);}')
    ioloop.start()


@with_ioloop
@with_couchdb
def test_temporary_view_nonempty_results(baseurl, ioloop):
    def do_test(db):
        def doc_ready(doc):
            db.temporary_view(view_results,
                              'function(doc) { emit(null, doc); }')

        def view_results(results):
            eq(len(results), 1)
            result = results[0]

            # Remove keys starting with _
            eq(
                dict((k, v) for k, v in result['value'].items() if k[0] != '_'),
                {'foo': 'bar'}
            )
            eq(result['key'], None)

            ioloop.stop()

        db.set('testid', {'foo': 'bar'}, doc_ready)

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_temporary_view_with_reduce_fun(baseurl, ioloop):
    def do_test(db):
        def doc_ready(doc):
            db.set({'value': 2}, doc2_ready)

        def doc2_ready(doc):
            db.temporary_view(
                view_results,
                map_fun='function(doc) { emit(null, doc.value); }',
                reduce_fun='function(key, values) { return sum(values); }'
            )

        def view_results(result):
            eq(result.error, False)
            eq(list(result), [{'key': None, 'value': 3}])
            ioloop.stop()

        db.set({'value': 1}, doc_ready)

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_copy_document(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            )

    def create_doc_callback(doc):
        doc.copy('newname', copy_done)

    def copy_done(doc):
        eq(doc.id, 'newname')
        eq(dict(doc), {'testvalue': 'something'})
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_copy_document_exists(baseurl, ioloop):
    def do_test(db):
        def create_doc(doc):
            db.set(
                {'testvalue': 'something'},
                copy_doc,
                )

        def copy_doc(doc):
            doc.copy('newname', copy_done)

        def copy_done(result):
            eq(result.error, True)
            eq(result.errno, trombi.errors.CONFLICT)
            eq(result.msg, 'Document update conflict.')
            ioloop.stop()

        db.set('newname', {'something': 'else'}, create_doc)

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_copy_document_with_attachments(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            attachments={'foo': (None, 'bar')}
            )

    def create_doc_callback(doc):
        doc.copy('newname', copy_done)

    def copy_done(doc):
        eq(doc.id, 'newname')
        eq(dict(doc), {'testvalue': 'something'})
        eq(doc.attachments.keys(), ['foo'])
        eq(doc.attachments['foo']['content_type'], 'text/plain')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_copy_loaded_document_with_attachments_false(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            attachments={'foo': (None, 'bar')}
            )

    def create_doc_callback(doc):
        doc.db.get(doc.id, got_doc)

    def got_doc(doc):
        doc.copy('newname', copy_done)

    def copy_done(doc):
        eq(doc.id, 'newname')
        eq(dict(doc), {'testvalue': 'something'})
        doc.load_attachment('foo', loaded_attachment)

    def loaded_attachment(attach):
        eq(attach, 'bar')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_copy_loaded_document_with_attachments_true(baseurl, ioloop):
    def create_db_callback(db):
        db.set(
            {'testvalue': 'something'},
            create_doc_callback,
            attachments={'foo': (None, 'bar')}
            )

    def create_doc_callback(doc):
        doc.db.get(doc.id, got_doc, attachments=True)

    def got_doc(doc):
        doc.copy('newname', copy_done)

    def copy_done(doc):
        eq(doc.id, 'newname')
        eq(dict(doc), {'testvalue': 'something'})
        eq(doc.attachments.keys(), ['foo'])
        eq(doc.attachments['foo']['content_type'], 'text/plain')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_list_with_results(baseurl, ioloop):
    def do_test(db):
        def create_view_callback(response):
            eq(response.code, 201)
            db.set({'data': 'data'}, create_doc_cb)

        def create_doc_cb(doc):
            db.list('testview', 'data', 'all', load_view_cb)

        def load_view_cb(result):
            print result
            eq(result.error, False)
            eq(result.content, 'data')
            ioloop.stop()

        db.server._fetch(
            '%stestdb/_design/testview' % baseurl,
            create_view_callback,
            method='PUT',
            body=json.dumps(
                {
                    'language': 'javascript',
                    'views': {
                        'all': {
                            'map': 'function (doc) { emit(null, doc) }',
                            }
                        },
                    'lists': {
                        'data': '''
function(head, req) {
    var row = getRow();
    send(row.value.data);
}
'''
                    }
                })
            )

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=do_test)
    ioloop.start()
