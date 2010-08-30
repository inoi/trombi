.. trombi documentation master file, created by
   sphinx-quickstart on Mon Aug 30 20:00:26 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to trombi's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2

   python-api


Introduction
============

Trombi provides an asynchronous CouchDB_ API for `tornado web server`_.
Motivation behind trombi was the lack of an asynchronous API to
CouchDB. As tornado ships with excellent :class:`AsyncHTTPClient`
and the CouchDB has an excellent RESTful API, making our own seemed
like a good idea.

Idea of trombi is to ship a simple to use API (in terms of simple
asynchronous APIs, of course) that requires minimum effort to use the
CouchDB in a tornado application. API has evolved a bit in the history
and probably will evolve in the future, so brace yourself for future
API changes, if you plan to use the bleeding edge trombi. The API
might still have some rough edges too but it is currently used in
production environment.

.. _CouchDB: http://couchdb.apache.org/

.. _tornado web server: http://tornadoweb.org/



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

