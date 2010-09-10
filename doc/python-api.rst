.. highlight:: python

.. _python-api:

*************
API Reference
*************

.. module:: trombi

This module consists of two different classes indicating query result,
:class:`TrombiObject` and :class:`TrombiError`, first for the
succesful API response and the latter for errorneus API response. All
classes representing different data objects of CouchDB_ subclass
:class:`TrombiObject`.

.. _CouchDB: http://couchdb.apache.org/

Result objects
==============

.. class:: TrombiError

   Returned upon errorneus CouchDB API call.

   .. attribute:: error

      Indicates that an error happened. Always *True*.

   .. attribute:: errno

      Error number. Trombi error numbers are available in
      :mod:`trombi.errors`. Unless something really odd happened,
      it's one of the following:

      .. attribute:: errors.BAD_REQUEST
                     errors.NOT_FOUND
                     errors.CONFLICT
                     errors.PRECONDITION_FAILED
                     errors.SERVER_ERROR

         These map to HTTP error codes respectively.

      .. attribute:: errors.INVALID_DATABASE_NAME

         A custom error code to distinct from overloaded
         :attr:`errors.SERVER_ERROR`. Means that the
         database name was invalid. **Note:** This can be returned
         without connecting to database, so your callback method might
         be called immediately without going back to the IOLoop.

   .. attribute:: msg

      Textual representation of error. This might be JSON_ as returned
      by CouchDB, but trombi makes no effort trying to decode it.

      .. _JSON: http://json.org/

.. class:: TrombiObject

   Returned upon succesful CouchDB call. This is also superclass for
   all data object classes presented below.

   .. attribute:: error

      Indicates succesful response, always *False*.

.. class:: TrombiResult

   A generic result indicating a succesfull call. Used for example in
   :meth:`Database.list`. Subclasses
   :class:`TrombiObject`.

   .. attribute:: content

      Contains the result of the query. The result format is not
      specified.

.. class:: ViewResult

   A special result object that represents a succesful view result.
   Subclasses :class:`TrombiObject` and
   :class:`collections.Sequence`.

   Due to the subclassing of :class:`collections.Sequence`, behaves
   kind of like a tuple. Supports :func:`len`, accessing items with
   dictionary like syntax and iterating over result rows using
   :func:`iter`.


Server
======

In case of an error, if not otherwise mentioned, all the following
methods call callback function with :class:`TrombiError` as an
argument.

.. class:: Server(baseurl[, fetch_args={}, io_loop=None])

   Represents the connection to a CouchDB server. Subclass of
   :class:`TrombiObject`.

   Has one required argument *baseurl* which is an URI to CouchDB
   database. If the *baseurl* ends in a slash (``/``), it is removed.

   To ease testing a custom :class:`tornado.ioloop.IOLoop` instance
   can be passed as a keyword argument.

   .. attribute:: baseurl
                  io_loop

      These two store the given arguments.

   .. attribute:: error

      Indicates an error, always *False*.

   .. attribute:: fetch_args

      Provides a way to pass in additional keyword arguments to the
      tornado's :meth:`AsyncHTTPClient.fetch()` call. In particular,
      by passing in ``auth_username`` and ``auth_password`` as keyword
      arguments, we can now use CouchDB servers using HTTP Basic
      Authentication.

   .. method:: create(name, callback)

      Creates a new database. Has two required arguments, the *name*
      of the new database and the *callback* function.

      On success the callback function is called with newly created
      :class:`Database` as an argument.

   .. method:: get(name, callback[, create=False])

      Tries to open database named *name*. Optional keyword argument
      *create* can be given to indicate that if the database does not
      exist, trombi tries to create it. As with
      :meth:`create`, calls the *callback* with a
      :class:`Database` on success.

   .. method:: delete(name, callback)

      Deletes a database named *name*. On success, calls *callback*
      with an empty :class:`TrombiObject` as an argument.

   .. method:: list(callback)

      Lists available databases. On success, calls *callback* with a
      generator object containing all databases.


Database
========

In case of an error, if not otherwise mentioned, all the following
methods call callback function with :class:`TrombiError` as an
argument.

.. class:: Database(server, name)

   Represents a CouchDB database. Has two required argument, *server*
   and *name* where *server* denotes the :class:`Server` where
   database is and *name* is the name of the database.

   Normally there's no need to create :class:`Database` objects
   as they are created via :meth:`Server.create` and
   :meth:`Server.get`. Subclass of :class:`TrombiObject`.

   .. method:: set([doc_id, ]data, callback[, attachments=None])

      Creates a new or modifies an existing document in the database.
      If called with three arguments, the first argument, *doc_id* is
      the document id of the new or existing document. If only two
      arguments are given the document id is generated by the
      database. *data* is the data to the document, either a Python
      :class:`dict` or an instance of :class:`Document`.
      *doc_id* can be omitted if *data* is an existing document.

      This method makes distinction between creating a new document
      and updating an existing by inspecting the *data* argument. If
      *data* is a :class:`Document` with attributes *rev* and
      *id* set, it tries to update existing document. Otherwise it
      tries to create a new document containing *data*.

      Inline attachments can be passed to function with optional
      keyword argument *attachments*. *attachments* is a :class:`dict`
      with a format somewhat similiar to CouchDB::

        {<attachment_name>: (<content_type>, <data>)}

      If *content_type* is None, ``text/plain`` is assumed.

      On succesful creation or update the *callback* is called with
      :class:`Document` as an argument.

   .. method:: get(doc_id, callback[, attachments=False)

      Loads a document *doc_id* from the database. If optional keyword
      argument *attachments* is given the inline attachments of the
      document are loaded.

      On success calls *callback* with :class:`Document` as an
      argument.

      **Note:** If there's no document with document id *doc_id* this
      function calls *callback* with argument *None*. Implementer
      should always check for *None* before checking the *error*
      attribute of the result object.

   .. method:: delete(doc, callback)

      Deletes a document in database. *doc* has to be a
      :class:`Document` with *rev* and *id* set or the deletion
      will fail.

      On success, calls *callback* with :class:`Database` (i.e.
      *self*) as an argument.

   .. method:: view(design_doc, viewname, callback[, **kwargs])

      Fetches view results from database. Both *design_doc* and
      *viewname* are string, which identify the view. Additional
      keyword arguments can be given and those are all sent as JSON
      encoded query parameters to CouchDB. For more information, see
      `CouchDB view API`_.

      **Note:** trombi does not yet support creating views through any
      special mechanism. Views should be created using
      :meth:`Database.set`.

      On success, a :class:`ViewResult` object is passed to
      *callback*.

      .. _CouchDB view API: http://wiki.apache.org/couchdb/HTTP_view_API

   .. method:: list(design_doc, listname, viewname, callback[, **kwargs])

      Fetches view, identified by *design_doc* and *listname*, results
      and filters them using the *listname* list function. Additional
      keyword arguments can be given and they are sent as query
      parameters to CouchDB.

      On success, a :class:`TrombiResult` object is passed to
      *callback*. Note that the response content is not defined in any
      way, it solely depends on the list function.

      Additional keyword arguments can be given and those are all sent
      as JSON encoded query parameters to CouchDB.

   .. method:: temporary_view(callback, map_fun[, reduce_fun=None, language='javascript', **kwargs])

      Generates a temporary view and on success calls *callback* with
      :class:`ViewResult` as an argument. For more information
      on creating map function *map_fun* and reduce function
      *reduce_fun* see `CouchDB view API`_.

      Additional keyword arguments can be given and those are all sent
      as JSON encoded query parameters to CouchDB.

Document
========

In case of an error, if not otherwise mentioned, all the following
methods call callback function with :class:`TrombiError` as an
argument.

.. class:: Document(db, data)

   This class represents a CouchDB document. This subclasses both
   :class:`collections.MutableMapping` and
   :class:`TrombiObject`. Has two mandatory arguments, a
   :class:`Database` intance *db* and *data*, which is a
   representation of document data as :class:`dict`.

   .. attribute:: db
                  data

      These two attribute store the given arguments

   .. attribute:: id
                  rev
                  attachments

      These contain CouchDB document id, revision and possible
      attachments.

   Normally there's no need to create Document objects as they are
   received as results of several different :class:`Database`
   operations.

   Document behaves like a :class:`dict` (not exactly, but not far
   anyway), as it implements an abstract base class
   :class:`collections.MutableMapping`.

   It supports :func:`len`, setting and getting values using the
   similiar notation as in dictionaries, e.g. ``doc[key] = val``. It
   also implements :func:`__contains__` so the presence of a key can
   be inspected using ``in`` operator.

   .. method:: copy(new_id, callback)

      Creates a copy of this document under new document id *new_id*.
      This operation is atomic as it is implemented using the custom
      ``COPY`` method provided by CouchDB.

      On success the *callback* function is called with a
      :class:`Document` denoting the newly created copy.

   .. method:: attach(name, data, callback[, type='text/plain'])

      Creates an attachment of name *name* to the document. *data* is
      the content of the attachment. These attachments are not so
      called inline attachments. *type* defaults to ``text/plain``.

      On success, *callback* is called with this
      :class:`Document` as an argument.

   .. method:: load_attachment(name, callback)

      Loads an attachment named *name*. On success the *callback* is
      called with the attachment data as an argument.

   .. method:: delete_attachment(name, callback)

      Deletes an attachment named *name*. On success, calls *callback*
      with this :class:`Document` as an argument.
