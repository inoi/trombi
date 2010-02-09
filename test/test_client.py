from __future__ import with_statement

from nose.tools import eq_ as eq
from couch_util import setup, teardown, with_couchdb
from util import with_ioloop, assert_raises

try:
    import json
except ImportError:
    import simplejson as json
import urllib

import tornadocouch
import tornadocouch.errors

@with_ioloop()
@with_couchdb
def test_create_db(couch_baseurl, tornado_baseurl, ioloop, application):
    def create_callback(db):
        assert isinstance(db, tornadocouch.Database)
        f = urllib.urlopen('%s_all_dbs' % couch_baseurl)
        eq(json.load(f), [db.name])
        ioloop.stop()


    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    s.create('couchdb-database', callback=create_callback)
    ioloop.start()

@with_ioloop()
@with_couchdb
def test_db_exists(couch_baseurl, tornado_baseurl, ioloop, application):
    def create_errback(errno, msg):
        eq(errno, tornadocouch.errors.ALREADY_EXISTS)
        eq(msg, "Database already exists: 'couchdb-database'")
        f = urllib.urlopen('%s_all_dbs' % couch_baseurl)
        eq(json.load(f), ['couchdb-database'])
        ioloop.stop()

    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    s.create('couchdb-database', callback=lambda x: x)
    s.create('couchdb-database', callback=lambda x: x, errback=create_errback)

    ioloop.start()

@with_ioloop()
@with_couchdb
def test_invalid_db_name(couch_baseurl, tornado_baseurl, ioloop, application):
    def errback(errno, msg):
        eq(errno, tornadocouch.errors.INVALID_DATABASE_NAME)
        eq(msg, "Invalid database name: 'this name is invalid'")
        ioloop.stop()

    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    s.create('this name is invalid', callback=lambda x: x, errback=errback)
    ioloop.start()

@with_ioloop()
@with_couchdb
def test_delete_db(couch_baseurl, tornado_baseurl, ioloop, application):
    def create_callback(db):
        db.delete(callback=delete_callback)

    def delete_callback():
        f = urllib.urlopen('%s_all_dbs' % couch_baseurl)
        eq(json.load(f), [])
        ioloop.stop()

    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    s.create('testdatabase', callback=create_callback)
    ioloop.start()

@with_ioloop()
@with_couchdb
def test_delete_db_not_exists(couch_baseurl, tornado_baseurl,
                              ioloop, application):
    def delete_errback(errno, msg):
        eq(errno, tornadocouch.errors.DOES_NOT_EXIST)
        eq(msg, "Database does not exist: 'testdatabase'")
        ioloop.stop()

    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    db = tornadocouch.Database(s, 'testdatabase')
    db.delete(callback=None, errback=delete_errback)
    ioloop.start()

@with_ioloop()
@with_couchdb
def test_list_databases(couch_baseurl, tornado_baseurl,
                              ioloop, application):
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

    s = tornadocouch.Server(couch_baseurl, io_loop=ioloop)
    s.create('testdb1', callback=create_first)
    ioloop.start()
