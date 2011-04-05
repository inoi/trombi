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

Helper methods
==============

.. method:: trombi.from_uri(uri[, fetch_args={}, io_loop=None, **kwargs])

   Constructs a :class:`Database` instance from *uri*. The *uri*
   format is the http-path to the database, for example
   ``http://localhost:5984/my-database``. Additional arguments can be
   given and they are passed to the :class:`Server` object upon
   creation.

Result objects
==============

.. class:: TrombiError

   A common error class indicating that an error has happened

   .. attribute:: error

      Indicates that error happened. Always *True*.

.. class:: TrombiErrorResponse

   Returned upon errorneus CouchDB API call. This is generally a call
   that results in other than 2xx response code.

   Subclasses :class:`TrombiError`.

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

   .. attribute:: total_rows

      Total rows of the view as returned by CouchDB

   .. attribute:: offset

      Offset of the view as returned by CouchDB

.. class:: BulkResult

   A special result object for CouchDB's bulk API responses.
   Subclasses :class:`TrombiObject` and :class:`collections.Sequence`.

   Due to the subclassing of :class:`collections.Sequence`, behaves
   kind of like a tuple. Supports :func:`len`, accessing items with
   dictionary like syntax and iterating over result :func:`iter`.

   .. attribute:: content

      The processed bulk API response content. Consists of instances
      of either :class:`BulkObject` or :class:`BulkError`.

.. class:: BulkObject

   A special result object for a single successful CouchDB's bulk API
   response. Subclasses :class:`TrombiObject` and
   :class:`collections.Mapping`.

   Due to the subclassing of :class:`collections.Mapping`, behaves
   like a immutable dictionary. Can be converted to a dictionary
   object using built-in function :func:`dict`.

.. class:: BulkError

   Indicates a single error response from bulk API. Subclasses
   :class:`TrombiError`.

   .. attribute:: error_type

      The error type given by bulk API

   .. attribute:: reason

      The reason given by bulk API


Server
======

In case of an error, if not otherwise mentioned, all the following
methods call callback function with :class:`TrombiError` as an
argument.

.. class:: Server(baseurl[, fetch_args={}, io_loop=None, json_encoder, **client_args])

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

   .. attribute:: json_encoder

      A custom json_encoder can be defined with parameter
      *json_encoder*. At this point, this encoder is only used when
      adding or modifying documents.

   .. attribute:: client_args

      These additional arguments are directly passed to the
      :meth:`AsyncHTTPClient` upon creation. This way the user can
      configure the underlying HTTP client, for example to allow more
      concurrent connections by passing
      ``max_simultaneous_connections`` keyword argument.

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

   .. method:: bulk_docs(bulk_data, callback[, all_or_nothing=False])

      Performs a bulk update on database. *bulk_data* is a list of
      :class:`Document` or :class:`dict` objects. If the upgrade was
      succesfull (i.e. returned with 2xx HTTP response code) calls
      *callback* with :class:`BulkResult` as a parameter.

      If *all_or_nothing* is *True* the operation is done with the
      *all_or_nothing* flag set to *true*. For more information, see
      `CouchDB bulk document API`_.

      .. _CouchDB bulk document API: http://wiki.apache.org/couchdb/HTTP_Bulk_Document_API

   .. method:: view(design_doc, viewname, callback[, **kwargs])

      Fetches view results from database. Both *design_doc* and
      *viewname* are string, which identify the view. Additional
      keyword arguments can be given and those are all sent as JSON
      encoded query parameters to CouchDB with one exception. If a
      keyword argument ``keys`` is given the query is transformed to
      *POST* and the payload will be JSON object ``{"keys": <keys>}``.
      For more information, see `CouchDB view API`_.

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

   .. method:: changes(callback[, feed_type='normal', timeout=60, **kw])

      Fetches the ``_changes`` feed for the database. Has two optional
      keyword arguments, *timeout* and *feed_type*. *timeout* is
      in seconds and defaults to 60 seconds, which is CouchDB's
      default timeout for changes feed. *feed_type* is described in
      `CouchDB database API`_. Additional keyword arguments are
      converted to query parameters for the changes feed. For possible
      keyword arguments, see `CouchDB database API`_ entry of changes
      feed.

      If *feed_type* is ``continous``, the callback is passed as
      both streaming and regular callback to the fetch function. The
      callback is called every time the changes feed sends a line of
      text that is JSON encoded. The argument to the callback is this
      line decoded. When the changes feed closes for some reason, the
      callback is called with *None* as an argument if the feed
      closed properly (ie. server closed the request with ``200 OK``).
      Otherwise the callback is called with the error object.

      .. _CouchDB database API: http://wiki.apache.org/couchdb/HTTP_database_API#Changes

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

   .. method:: raw()

      Returns the document's content as a raw dict, containing
      CouchDB's internal variables like _id and _rev.

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

Paginator
=========

.. class:: Paginator(db[, limit=10])

   Represents a pseudo-page of documents returned from a CouchDB view
   calculated from total_rows and offset as well as a user-defined page
   limit.

   The one mandatory argument, db, is a :class:`Database` instance.  

   .. attribute:: db

      Stores the given argument.

   .. attribute:: limit

      The number of documents returned for a given "page"

   .. attribute:: response

      Stores the actual :class:`ViewResult` instance.

   .. attribute:: count

      The total_rows attribute returned from the CouchDB view

   .. attribute:: start_index

      The document offset or position of the first item on the page.

   .. attribute:: end_index

      The document offset or position of the last item on the page.

   .. attribute:: num_pages

      The total number of pages (total_rows of view / limit)

   .. attribute:: current_page

      The current page number

   .. attribute:: previous_page

      The previous page number

   .. attribute:: next_page

      The next page number

   .. attribute:: rows

      An ordered array of the documents for the current page

   .. attribute:: has_next

      A Boolean member to determine if there is a next page

   .. attribute:: has_previous

      A Boolean member to determine if there is a previous page

   .. attribute:: page_range

      A list of the number of pages

   .. attribute:: start_doc_id

      The Document ID of the first document on the page

   .. attribute:: end_doc_id

      The Document ID of the last document on the page

   .. method:: get_page(design_doc, viewname, callback[, key=None, doc_id=None, forward=True, **kwargs])

      Fetches the ``limit`` specified number of CouchDB documents from
      the view.

      ``key`` can be defined as a complex key by the calling function.
      If requesting a previous page, the ``key`` must be built using the
      first document on the current page.  If requesting the next page,
      ``key`` must be built using the last document on the current page.

      ``doc_id`` uses the same logic as the above key, but is used to
      specify start_doc_id or end_doc_id (depending on forward) in
      case the CouchDB view returns duplicate keys.

      ``forward`` simply defines whether you are requesting to go
      to the next page or the previous page.  If ``forward`` is False then
      it attempts to move backward from the key/doc_id given.  If
      ``forward`` is True then it attempts to more forward.

      Additional keyword arguments can be given and those are all sent
      as JSON encoded query parameters to CouchDB and can override
      default values such as descending = true.

      On success, *callback* is called with this :class:`Paginator` as
      an argument.

