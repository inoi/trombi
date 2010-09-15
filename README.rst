Trombi README
=============

Trombi is an asynchronous CouchDB_ client for Tornado_.

*trombi* is Finnish for a small tornado, occuring in Europe.


Requirements
------------

* Python_ 2.6+

* Tornado_ 1.0+

For running tests:

* couchdb-python_

* nose_


Documentation
-------------

Documentation created using Sphinx_ is available in *doc/* directory.
Compiling documentation requires version 0.6.x of Sphinx.

Online documentation can be seen on `Github pages`_.

Issues are reported in `Github`_ and there's also `a mailing list`_
available in Google Groups.

Example program
---------------

::

    import trombi
    from tornado.ioloop import IOLoop

    def main():
        server = trombi.Server('http://localhost:5984')
        server.get('my_database', database_created, create=True)

    def database_created(db):
        if db.error:
            print 'Unable to create database!'
            print db.msg
            ioloop.stop()
        else:
            db.set('my_document', {'testvalue': 'something'}, doc_created)

    def doc_created(doc):
        if doc.error:
            print 'Unable to create document!'
            print doc.msg
        else:
            print 'Doc added!'

        ioloop.stop()

    if __name__ == '__main__':
        ioloop = IOLoop.instance()
        ioloop.add_callback(main)
        ioloop.start()


More usage examples can be found in tests.

License
-------

Trombi is licensed under MIT License. See *LICENSE* for more
information.

.. _CouchDB: http://couchdb.apache.org/

.. _Python: http://python.org/

.. _Tornado: http://tornadoweb.org/

.. _couchdb-python: http://code.google.com/p/couchdb-python/

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/

.. _sphinx: http://sphinx.pocoo.org/

.. _github pages: http://inoi.github.com/trombi/

.. _Github: http://github.com/inoi/trombi/

.. _a mailing list: http://groups.google.com/group/python-trombi?lnk=gcimh
