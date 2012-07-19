tw2.sqla
========


Introduction
------------

tw2.sqla is a database layer for ToscaWidgets 2 and SQLAlchemy. It allows common database tasks to be achieved with minimal code. There are four main features:

 * Session and transaction management
 * Loading and saving data
 * Populating selection fields
 * Generating widget definitions

See the :ref:`design` document for a more detailed description of these. 

tw2.sqla is designed to work fully however you define your model objects - traditional, declarative base, or Elixir.


Getting started
---------------

If you are using tw2.sqla with another framework (e.g. Pyramid), the framework will already be providing session management. You do not need to use the session management within tw2.sqla. However, database objects used with tw2.sqla must have a ``query`` property.

For standalone tw2.sqla, the repoze.tm middleware needs to be installed in the stack. This can be done by passing ``repoze_tm=True`` to ``tw2.core.make_middleware`` or ``tw2.devtools.dev_server``. For example::

    tw2.devtools.dev_server(host='127.0.0.1', repoze_tm=True)

To set the query property to use ``ZopeTransactionExtension``, appropriate code must be added to your model. The examples below are for standalone tw2.sqla.

For declarative base::

    from sqlalchemy.ext.declarative import declarative_base
    import tw2.sqla as tws
    Base = declarative_base()
    Base.query = tws.transactional_session().query_property()

For Elixir::

    import elixir as el, tw2.sqla as tws
    el.session = tws.transactional_session()

Once this is setup, the application does not need to explicitly deal with sessions.

**TBD** Provide further examples for other frameworks.


Loading and Saving Data
-----------------------

There are several `Page` subclasses that automatically load and save data. Each have an `entity` property that must be set to an SQLAlchemy object.

`tw2.sqla.DbListPage`
    
    This presents a list of items.
    
`tw2.sqla.DbFormPage`

    This allows editing of a single item. The item is loaded based on primary key columns in the query string. When the form is posted, the data is saved back to the database. The user is redirected to the URL specified by the `redirect` parameter.
    
`tw2.sqla.DbListForm`
    
    This allows editing of a multiple items, e.g. allow you to edit a whole list of users. This may be removed in future, if a way is found to incorporate this functionality with `DbFormPage`.

In addition, `tw2.sqla.DbLinkField` can be used to generate a link to a `DbFormPage`. It adds all the primary key columns from an object to the query string.

**TBD** There is no way to filter what is displayed in the list - although a partial workaround is to map the underlying SQLAlchemy object to a select statement, which performs the filtering. Also, DbFormPage has no protection against parameter tampering.


Populating selection fields
---------------------------

`DbSelectionField` automatically loads it's contents from a database table. It has an `entity` property that must be set to an SQLAlchemy object. The subclasses are:

 * DbSingleSelectField
 * DbRadioList
 * DbCheckBoxList
 * DbCheckBoxTable

Note: composite primary keys are **not** supported by these fields. 

Internally it uses ``tw2.sqla.RelatedValidator`` which converts ID values to and from objects. You must always apply the widget to a relation, not the underlying column. For example::

    class User(Base):
        group_name = sa.Column(sa.String(), sa.ForeignKey('group'))
        group = sao.relationship('Group')

    class UserForm(twf.TableForm):
        group = tws.DbSingleSelectField(entity=Group)

**TBD** There is no way to filter what is displayed in the list - although a partial workaround is to map the underlying SQLAlchemy object to a select statement, which performs the filtering. Also, there is no protection against parameter tampering.


Automatic widgets
-----------------

`WidgetPolicy` generates widgets from SQLAlchemy property objects. It uses the column type, name, and attributes such as nullable. Two subclasses are provided: `ViewPolicy` and `EditPolicy`. For example, EditPolicy generates SQLAlchemy Date columns as `CalendarDataPicker` widgets. Users can further subclass these policies to suit their own needs.

`AutoContainer` is a widget that generates its own children automatically, using an SQLAlchemy model object, and a `WidgetPolicy`. Several subclasses are provided:

 * AutoTableForm
 * AutoGrowingGrid
 * AutoViewGrid
 * AutoViewFieldSet
 * AutoEditFieldSet 
 
For example::

    class MyForm(tws.AutoTableForm):
        entity = model.MyObject

Individual fields can be overridden. For example, if `address` is automatically generated as a `TextField` but you need a `TextArea`, do this::

    class MyForm(tws.AutoTableForm):
        entity = model.MyObject
        address = twf.TextArea()

To suppress a field, use `tws.NoWidget`.

.. autoclass:: tw2.sqla.WidgetPolicy

**TBD**
 
 * Sometimes you want a way to say "only include these fields"
 * Hints on the model, using the info attribute - experimental; needs tests & doc
 * There are experimental widgets for `AutoListPage` and `AutoListPageEdit`. The biggest issue is linking between them.


Contents
--------

.. toctree::
   :maxdepth: 1

   design
