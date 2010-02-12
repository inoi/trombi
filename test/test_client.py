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

import tornadocouch
import tornadocouch.errors

@with_ioloop
@with_couchdb
def test_create_db(baseurl, ioloop):
    def create_callback(db):
        assert isinstance(db, tornadocouch.Database)
        f = urllib.urlopen('%s_all_dbs' % baseurl)
        eq(json.load(f), [db.name])
        ioloop.stop()


    s = tornadocouch.Server(baseurl, io_loop=ioloop)
    s.create('couchdb-database', callback=create_callback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_db_exists(baseurl, ioloop):
    s = tornadocouch.Server(baseurl, io_loop=ioloop)

    def first_callback(db):
        s.create(
            'couchdb-database',
            callback=None,
            errback=create_errback
            )

    def create_errback(errno, msg):
        eq(errno, tornadocouch.errors.PRECONDITION_FAILED)
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
        eq(errno, tornadocouch.errors.INVALID_DATABASE_NAME)
        eq(msg, "Invalid database name: 'this name is invalid'")
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
    s.create('this name is invalid', callback=lambda x: x, errback=errback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_delete_db(baseurl, ioloop):
    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        eq(errno, tornadocouch.errors.NOT_FOUND)
        eq(msg, "Database does not exist: 'testdatabase'")
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        assert all(isinstance(x, tornadocouch.Database) for x in databases)
        eq(
            ['testdb2', 'testdb1'],
            [x.name for x in databases],
            )
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
    s.create('testdb1', callback=create_first)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_database(baseurl, ioloop):
    s = tornadocouch.Server(baseurl, io_loop=ioloop)

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
    s = tornadocouch.Server(baseurl, io_loop=ioloop)

    def load_errback(errno, msg):
        eq(errno, tornadocouch.errors.NOT_FOUND)
        eq(msg, "Database not found: 'testdb1'")
        ioloop.stop()

    s.load('testdb1', callback=None, errback=load_errback)
    ioloop.start()

@with_ioloop
@with_couchdb
def test_open_database_bad_name(baseurl, ioloop):
    s = tornadocouch.Server(baseurl, io_loop=ioloop)

    def load_errback(errno, msg):
        eq(errno, tornadocouch.errors.INVALID_DATABASE_NAME)
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
        assert isinstance(doc, tornadocouch.Document)
        assert doc.id
        assert doc.rev

        eq(doc['testvalue'], 'something')
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        assert isinstance(doc, tornadocouch.Document)
        assert doc.id
        assert doc.rev

        eq(doc.id, 'something/with/slash')
        eq(doc['testvalue'], 'something')
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        assert isinstance(doc, tornadocouch.Document)
        assert doc.id
        assert doc.rev

        eq(doc['testvalue'], 'something')
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        assert isinstance(doc, tornadocouch.Document)
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

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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
        eq(errno, tornadocouch.errors.CONFLICT)
        eq(msg, 'Document update conflict.')
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()


@with_ioloop
@with_couchdb
def test_load_document_does_not_exist(baseurl, ioloop):
    def create_db_callback(db):
        db.load('foo', callback=None, errback=load_errback)

    def load_errback(errno, msg):
        eq(errno, tornadocouch.errors.NOT_FOUND)
        eq(msg, 'missing')
        ioloop.stop()

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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



    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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



    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
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

    s = tornadocouch.Server(baseurl, io_loop=ioloop)
    s.create('testdb', callback=create_db_callback)
    ioloop.start()

