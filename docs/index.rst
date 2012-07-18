tw2.sqla
========


Introduction
------------

tw2.sqla is a database layer for ToscaWidgets 2 and SQLAlchemy. It allows common database tasks to be achieved with minimal code. There are four main features:

 * Session and transaction management
 * Loading and saving data
 * Populating selection fields
 * Generating widget definitions

See the :ref:`design` document for a more detailed description of these. tw2.sqla is designed to work fully however you define your model objects - traditional, declarative base, or Elixir.


.. warning::
    tw2.sqla itself is in good shape, but this document is out of date.



Getting started
---------------

If you are using tw2.sqla with another framework (e.g. Pyramid), the framework will already be providing session management. You do not need to use the session management within tw2.sqla.

Any database objects used with tw2.sqla must have a ``query`` property. This is automatically present with Elixir. For declarative base, you must use the following::

    Base = declarative_base()
    Base.query = tws.transactional_session().query_property()


Session and Transaction Management
----------------------------------

The repoze.tm middleware needs to be installed in the stack. This can be done by passing ``repoze_tm=True`` to ``tw2.core.make_middleware`` or ``tw2.devtools.dev_server``. For example::

    tw2.devtools.dev_server(host='127.0.0.1', repoze_tm=True)

For this to work correctly, ``ZopeTransactionExtension`` must be installed in the session; there is a convenience function for this ``tw2.sqla.transactional_session``

To use this with Elixir, add the following to the model file::

    import elixir as el, tw2.sqla as tws
    el.session = tws.transactional_session()

With declarative base, if the query property is setup as above, no further configuration is necessary.


Loading and Saving Data
-----------------------

The main classes to use are:

`tw2.sqla.DbListPage`
    
    This presents a list of items.
    
`tw2.sqla.DbFormPage`

    This allows editing of a single item. The item is loaded based on primary key columns in the query string. When the form is posted, the data is saved back to the database.
    
Internally, ``tw2.sqla.RelatedValidator`` is key - it converts IDs to objects. Other classes to use: `DbListForm` and `DbLinkField`.


Populating selection fields
---------------------------

Main classes:

 * DbSingleSelectField
 * DbRadioList
 * DbCheckBoxList
 * DbCheckBoxTable

Note: composite primary keys are NOT supported by these fields.


Generating Widget Definitions
-----------------------------

There is a policy class that defines the widget and its characteristics, based on:

 * Database type
 * Field name (e.g. password, email)
 * Database details, e.g. nullable

For relations:

 * ManyToOne - SingleSelectField
 * ManyToMany - CheckBoxList
 * OneToMany - nothing



**Contents**

.. toctree::
   :maxdepth: 2

   design
