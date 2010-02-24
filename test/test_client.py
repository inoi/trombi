# Copyright (c) Inoi Oy 2010. All rights reserved.
#
# This material constitutes a trade secret of Inoi Oy.
#
# The software, manuals, and technical literature of
# Inoi Oy products may not be reproduced in any form or
# by any means except by permission in writing from
# Inoi Oy.

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

@with_ioloop
@with_couchdb
def test_create_db(baseurl, ioloop):
    def create_callback(db):
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
            callback=None,
            errback=create_errback
            )

    def create_errback(errno, msg):
        eq(errno, trombi.errors.PRECONDITION_FAILED)
        eq(msg, "Database already exists: 'couchdb-database'")
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), ['couchdb-database'])
        ioloop.stop()

    s.create('couchdb-database', callback=first_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_invalid_db_name(baseurl, ioloop):
    def errback(errno, msg):
        eq(errno, trombi.errors.INVALID_DATABASE_NAME)
        eq(msg, "Invalid database name: 'this name is invalid'")
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('this name is invalid', callback=lambda x: x, errback=errback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_db(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)
    def create_callback(db):
        s.delete('testdatabase', callback=delete_callback)

    def delete_callback():
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), [])
        ioloop.stop()

    s.create('testdatabase', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_db_not_exists(baseurl, ioloop):
    def delete_errback(errno, msg):
        eq(errno, trombi.errors.NOT_FOUND)
        eq(msg, "Database does not exist: 'testdatabase'")
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.delete('testdatabase', callback=None, errback=delete_errback)
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
        s.load('testdb1', callback=load_callback)

    def load_callback(db):
        eq(db.name, 'testdb1')
        eq(db.server, s)
        ioloop.stop()

    s.create('testdb1', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_nonexisting_database(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def load_errback(errno, msg):
        eq(errno, trombi.errors.NOT_FOUND)
        eq(msg, "Database not found: 'testdb1'")
        ioloop.stop()

    s.load('testdb1', callback=None, errback=load_errback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_database_bad_name(baseurl, ioloop):
    s = trombi.Server(baseurl, io_loop=ioloop)

    def load_errback(errno, msg):
        eq(errno, trombi.errors.INVALID_DATABASE_NAME)
        eq(msg, "Invalid database name: 'not a valid name'")
        ioloop.stop()

    s.load('not a valid name', callback=None, errback=load_errback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_document(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            )

    def create_doc_callback(doc):
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
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='something/with/slash',
            )

    def create_doc_callback(doc):
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
def test_load_document(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=functools.partial(create_doc_callback, db=db)
            )

    def create_doc_callback(doc, db=None):
        db.load(doc.id, callback=load_doc_callback)

    def load_doc_callback(doc):
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
def test_create_document_custom_id(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='testid',
            )

    def create_doc_callback(doc):
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

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_document(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=functools.partial(create_doc_callback, db),
            doc_id='testid'
            )

    def create_doc_callback(db, doc):
        db.delete(doc, callback=delete_doc_callback)

    def delete_doc_callback(db):
        assert isinstance(db, trombi.Database)
        ioloop.stop()

        f = urllib.urlopen('%stestdb/testid' % baseurl)
        eq(f.getcode(), 404)

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_document_not_existing(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=functools.partial(create_doc_callback, db),
            doc_id='testid'
            )

    def create_doc_callback(db, doc):
        doc.id = 'wrongid'
        db.delete(doc, callback=None, errback=delete_doc_errback)

    def delete_doc_errback(errno, msg):
        eq(errno, trombi.errors.NOT_FOUND)
        eq(msg, 'missing')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_delete_document_wrong_rev(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=functools.partial(create_doc_callback, db),
            doc_id='testid'
            )

    def create_doc_callback(db, doc):
        doc.rev = 'wrong'
        db.delete(doc, callback=None, errback=delete_doc_errback)

    def delete_doc_errback(errno, msg):
        eq(errno, trombi.errors.SERVER_ERROR)
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_create_document_custom_id_exists(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=functools.partial(create_1st_doc_callback, db=db),
            doc_id='testid',
            )

    def create_1st_doc_callback(doc, db):
        db.create(
            {'testvalue': 'something'},
            None,
            doc_id='testid',
            errback=create_doc_error,
            )
    def create_doc_error(errno, msg):
        eq(errno, trombi.errors.CONFLICT)
        eq(msg, 'Document update conflict.')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_document_does_not_exist(baseurl, ioloop):
    def create_db_callback(db):
        db.load('foo', callback=None, errback=load_errback)

    def load_errback(errno, msg):
        eq(errno, trombi.errors.NOT_FOUND)
        eq(msg, 'missing')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_save_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='testid',
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
def test_save_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='testid',
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
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='testid',
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
def test_delete_attachment(baseurl, ioloop):
    def create_db_callback(db):
        db.create(
            {'testvalue': 'something'},
            callback=create_doc_callback,
            doc_id='testid',
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
    def create_db_callback(db):
        def create_view_callback(response):
            eq(response.code, 201)
            db.view('testview', 'all', load_view_cb)

        db.server.client.fetch(
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

    def load_view_cb(result):
        assert isinstance(result, list)
        eq(result, [])
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_view_with_results(baseurl, ioloop):
    def create_db_callback(db):
        def create_doc_cb(doc):
            db.view('testview', 'all', load_view_cb)

        def create_view_callback(response):
            eq(response.code, 201)
            db.create({'data': 'data'}, create_doc_cb)

        db.server.client.fetch(
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

    def load_view_cb(result):
        assert isinstance(result, list)
        eq(len(result), 1)
        result[0]['value'].pop('_rev')
        result[0]['value'].pop('_id')
        result[0].pop('id')
        eq(result, [{'value': {'data': 'data'}, 'key': None}])
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_view_with_grouping_reduce(baseurl, ioloop):
    def create_db_callback(db):
        times = 0
        def create_doc_cb(doc):
            if doc['data'] == 'other':
                db.view('testview', 'all', load_view_cb, group='true')
            else:
                db.create({'data': 'other'}, create_doc_cb)

        def create_view_callback(response):
            eq(response.code, 201)
            db.create({'data': 'data'}, create_doc_cb)

        db.server.client.fetch(
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

    def load_view_cb(result):
        assert isinstance(result, list)
        eq(result, [{'value': 1, 'key': 'data'},
                    {'value': 1, 'key': 'other'}])
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_load_view_no_design_doc(baseurl, ioloop):
    def create_db_callback(db):
        def load_view_eb(errno, msg):
            eq(errno, trombi.errors.NOT_FOUND)
            eq(msg, 'missing')
            ioloop.stop()
        db.view('testview', 'all', None, errback=load_view_eb, group='true')


    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_view_no_such_view(baseurl, ioloop):
    def create_db_callback(db):
        def create_view_callback(useless):
            db.view('testview', 'all', None, errback=load_view_eb)

        db.server.client.fetch(
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
    def load_view_eb(errno, msg):
        eq(errno, trombi.errors.NOT_FOUND)
        eq(msg, 'missing_named_view')
        ioloop.stop()

    s = trombi.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

